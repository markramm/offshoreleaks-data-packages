"""Tests for the query builder and templates."""

from offshore_leaks_mcp.queries import OffshoreLeaksQueries, QueryBuilder


class TestQueryBuilder:
    """Test the QueryBuilder utility class."""

    def test_escape_string(self) -> None:
        """Test string escaping."""
        assert QueryBuilder.escape_string("normal") == "normal"
        assert QueryBuilder.escape_string("quote's test") == "quote\\'s test"
        assert (
            QueryBuilder.escape_string('double "quote" test')
            == 'double \\"quote\\" test'
        )

    def test_build_where_conditions_empty(self) -> None:
        """Test building WHERE conditions with no conditions."""
        where_clause, parameters = QueryBuilder.build_where_conditions("n", {})

        assert where_clause == ""
        assert parameters == {}

    def test_build_where_conditions_basic(self) -> None:
        """Test building WHERE conditions with basic equality."""
        conditions = {"name": "Test Entity", "status": "Active"}
        where_clause, parameters = QueryBuilder.build_where_conditions("e", conditions)

        assert "WHERE" in where_clause
        assert "e.name = $param_0" in where_clause
        assert "e.status = $param_1" in where_clause
        assert "AND" in where_clause
        assert parameters["param_0"] == "Test Entity"
        assert parameters["param_1"] == "Active"

    def test_build_where_conditions_contains(self) -> None:
        """Test building WHERE conditions with contains matching."""
        conditions = {"name_contains": "Test"}
        where_clause, parameters = QueryBuilder.build_where_conditions("e", conditions)

        assert "toLower(e.name) CONTAINS toLower($param_0)" in where_clause
        assert parameters["param_0"] == "Test"

    def test_build_where_conditions_date_range(self) -> None:
        """Test building WHERE conditions with date ranges."""
        conditions = {
            "incorporation_date_from": "2020-01-01",
            "incorporation_date_to": "2020-12-31",
        }
        where_clause, parameters = QueryBuilder.build_where_conditions("e", conditions)

        assert "e.incorporation_date >= date($param_0)" in where_clause
        assert "e.incorporation_date <= date($param_1)" in where_clause
        assert parameters["param_0"] == "2020-01-01"
        assert parameters["param_1"] == "2020-12-31"

    def test_build_where_conditions_skip_none(self) -> None:
        """Test that None and empty values are skipped."""
        conditions = {"name": "Test", "status": None, "country": ""}
        where_clause, parameters = QueryBuilder.build_where_conditions("e", conditions)

        assert "e.name = $param_0" in where_clause
        assert "status" not in where_clause
        assert "country" not in where_clause
        assert len(parameters) == 1


class TestOffshoreLeaksQueries:
    """Test the OffshoreLeaksQueries class."""

    def test_search_entities_basic(self) -> None:
        """Test basic entity search query."""
        query, params = OffshoreLeaksQueries.search_entities(
            name="Test Entity", limit=10, offset=5
        )

        assert "MATCH (e:Entity)" in query
        assert "WHERE" in query
        assert "toLower(e.name) CONTAINS toLower(" in query
        assert "ORDER BY e.name" in query
        assert "SKIP $offset" in query
        assert "LIMIT $limit" in query
        assert params["limit"] == 10
        assert params["offset"] == 5

    def test_search_entities_full_params(self) -> None:
        """Test entity search with all parameters."""
        query, params = OffshoreLeaksQueries.search_entities(
            name="Test",
            jurisdiction="BVI",
            country_codes="VG",
            company_type="Corporation",
            status="Active",
            incorporation_date_from="2020-01-01",
            incorporation_date_to="2020-12-31",
            source="Paradise Papers",
            limit=20,
            offset=0,
        )

        assert "MATCH (e:Entity)" in query
        assert "WHERE" in query
        assert (
            len([p for p in params.keys() if p.startswith("param_")]) == 8
        )  # 8 search conditions
        assert params["limit"] == 20
        assert params["offset"] == 0

    def test_search_officers_basic(self) -> None:
        """Test basic officer search query."""
        query, params = OffshoreLeaksQueries.search_officers(name="John Doe", limit=15)

        assert "MATCH (o:Officer)" in query
        assert "WHERE" in query
        assert "toLower(o.name) CONTAINS toLower(" in query
        assert "ORDER BY o.name" in query
        assert params["limit"] == 15

    def test_search_intermediaries_basic(self) -> None:
        """Test basic intermediary search query."""
        query, params = OffshoreLeaksQueries.search_intermediaries(
            name="Law Firm", countries="USA"
        )

        assert "MATCH (i:Intermediary)" in query
        assert "WHERE" in query
        assert "toLower(i.name) CONTAINS toLower(" in query
        assert "toLower(i.countries) CONTAINS toLower(" in query

    def test_get_entity_details_basic(self) -> None:
        """Test entity details query without relationships."""
        query, params = OffshoreLeaksQueries.get_entity_details(
            "entity_123", include_relationships=False
        )

        assert "MATCH (e:Entity {node_id: $node_id})" in query
        assert "RETURN e, [] as relationships" in query
        assert params["node_id"] == "entity_123"

    def test_get_entity_details_with_relationships(self) -> None:
        """Test entity details query with relationships."""
        query, params = OffshoreLeaksQueries.get_entity_details(
            "entity_123", include_relationships=True
        )

        assert "MATCH (e:Entity {node_id: $node_id})" in query
        assert "OPTIONAL MATCH (e)-[r]-(related)" in query
        assert "collect(DISTINCT" in query
        assert params["node_id"] == "entity_123"

    def test_get_connections_basic(self) -> None:
        """Test basic connections query."""
        query, params = OffshoreLeaksQueries.get_connections(
            start_node_id="node_123", max_depth=2, limit=25
        )

        assert "MATCH (start {node_id: $start_node_id})" in query
        assert "MATCH path = (start)-[r*1..$max_depth]-(connected)" in query
        assert "WHERE connected.node_id <> $start_node_id" in query
        assert "ORDER BY distance, connected.name" in query
        assert params["start_node_id"] == "node_123"
        assert params["max_depth"] == 2
        assert params["limit"] == 25

    def test_get_connections_with_filters(self) -> None:
        """Test connections query with relationship and node type filters."""
        query, params = OffshoreLeaksQueries.get_connections(
            start_node_id="node_123",
            relationship_types=["officer_of", "connected_to"],
            node_types=["Entity", "Officer"],
            max_depth=3,
        )

        assert ":officer_of|connected_to" in query
        assert (
            "'Entity' IN labels(connected) OR 'Officer' IN labels(connected)" in query
        )

    def test_get_statistics_overview(self) -> None:
        """Test statistics query for overview."""
        query, params = OffshoreLeaksQueries.get_statistics("overview")

        assert "MATCH (e:Entity)" in query
        assert "MATCH (o:Officer)" in query
        assert "MATCH (i:Intermediary)" in query
        assert "count(e) as entity_count" in query
        assert params == {}

    def test_get_statistics_by_source(self) -> None:
        """Test statistics query by source."""
        query, params = OffshoreLeaksQueries.get_statistics("by_source")

        assert "MATCH (n)" in query
        assert "WHERE n.sourceID IS NOT NULL" in query
        assert "n.sourceID as source" in query
        assert "labels(n)[0] as node_type" in query

    def test_get_statistics_by_jurisdiction(self) -> None:
        """Test statistics query by jurisdiction."""
        query, params = OffshoreLeaksQueries.get_statistics("by_jurisdiction")

        assert "MATCH (e:Entity)" in query
        assert "WHERE e.jurisdiction IS NOT NULL" in query
        assert "e.jurisdiction as jurisdiction" in query
        assert "LIMIT 50" in query

    def test_get_statistics_relationship_counts(self) -> None:
        """Test statistics query for relationship counts."""
        query, params = OffshoreLeaksQueries.get_statistics("relationship_counts")

        assert "MATCH ()-[r]->()" in query
        assert "type(r) as relationship_type" in query
        assert "ORDER BY count DESC" in query

    def test_get_statistics_unknown_type(self) -> None:
        """Test statistics query with unknown type defaults to node counts."""
        query, params = OffshoreLeaksQueries.get_statistics("unknown_type")

        assert "MATCH (n)" in query
        assert "labels(n)[0] as node_type" in query
        assert "ORDER BY count DESC" in query
