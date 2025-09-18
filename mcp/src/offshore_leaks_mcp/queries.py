"""Cypher query templates for the offshore leaks database."""

from typing import Any, Dict, List, Optional


class QueryBuilder:
    """Builder for safe Cypher queries with parameter validation."""

    @staticmethod
    def escape_string(value: str) -> str:
        """Escape string values for Cypher queries."""
        # Replace single quotes with escaped single quotes
        return value.replace("'", "\\'").replace('"', '\\"')

    @staticmethod
    def build_where_conditions(
        node_var: str, conditions: Dict[str, Any], prefix: str = "WHERE"
    ) -> tuple[str, Dict[str, Any]]:
        """Build WHERE conditions with parameterized queries."""
        where_parts = []
        parameters = {}
        param_counter = 0

        for field, value in conditions.items():
            if value is not None and value != "":
                param_name = f"param_{param_counter}"

                if field.endswith("_contains"):
                    # Handle partial string matching
                    actual_field = field.replace("_contains", "")
                    where_parts.append(
                        f"toLower({node_var}.{actual_field}) CONTAINS toLower(${param_name})"
                    )
                    parameters[param_name] = str(value)
                elif field.endswith("_from"):
                    # Handle date range (from)
                    actual_field = field.replace("_from", "")
                    where_parts.append(
                        f"{node_var}.{actual_field} >= date(${param_name})"
                    )
                    parameters[param_name] = str(value)
                elif field.endswith("_to"):
                    # Handle date range (to)
                    actual_field = field.replace("_to", "")
                    where_parts.append(
                        f"{node_var}.{actual_field} <= date(${param_name})"
                    )
                    parameters[param_name] = str(value)
                else:
                    # Exact match
                    where_parts.append(f"{node_var}.{field} = ${param_name}")
                    parameters[param_name] = value

                param_counter += 1

        if where_parts:
            where_clause = f" {prefix} " + " AND ".join(where_parts)
        else:
            where_clause = ""

        return where_clause, parameters


class OffshoreLeaksQueries:
    """Cypher queries for the offshore leaks database."""

    @staticmethod
    def search_entities(
        name: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        country_codes: Optional[str] = None,
        company_type: Optional[str] = None,
        status: Optional[str] = None,
        incorporation_date_from: Optional[str] = None,
        incorporation_date_to: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[str, Dict[str, Any]]:
        """Build entity search query."""
        conditions = {}

        if name:
            conditions["name_contains"] = name
        if jurisdiction:
            conditions["jurisdiction_contains"] = jurisdiction
        if country_codes:
            conditions["country_codes_contains"] = country_codes
        if company_type:
            conditions["company_type"] = company_type
        if status:
            conditions["status"] = status
        if incorporation_date_from:
            conditions["incorporation_date_from"] = incorporation_date_from
        if incorporation_date_to:
            conditions["incorporation_date_to"] = incorporation_date_to
        if source:
            conditions["sourceID"] = source

        where_clause, parameters = QueryBuilder.build_where_conditions("e", conditions)

        # Add pagination parameters
        parameters["limit"] = limit
        parameters["offset"] = offset

        query = f"""
        MATCH (e:Entity)
        {where_clause}
        RETURN e
        ORDER BY e.name
        SKIP $offset
        LIMIT $limit
        """

        return query.strip(), parameters

    @staticmethod
    def search_officers(
        name: Optional[str] = None,
        countries: Optional[str] = None,
        country_codes: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[str, Dict[str, Any]]:
        """Build officer search query."""
        conditions = {}

        if name:
            conditions["name_contains"] = name
        if countries:
            conditions["countries_contains"] = countries
        if country_codes:
            conditions["country_codes_contains"] = country_codes
        if source:
            conditions["sourceID"] = source

        where_clause, parameters = QueryBuilder.build_where_conditions("o", conditions)

        # Add pagination parameters
        parameters["limit"] = limit
        parameters["offset"] = offset

        query = f"""
        MATCH (o:Officer)
        {where_clause}
        RETURN o
        ORDER BY o.name
        SKIP $offset
        LIMIT $limit
        """

        return query.strip(), parameters

    @staticmethod
    def search_intermediaries(
        name: Optional[str] = None,
        countries: Optional[str] = None,
        country_codes: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[str, Dict[str, Any]]:
        """Build intermediary search query."""
        conditions = {}

        if name:
            conditions["name_contains"] = name
        if countries:
            conditions["countries_contains"] = countries
        if country_codes:
            conditions["country_codes_contains"] = country_codes
        if source:
            conditions["sourceID"] = source

        where_clause, parameters = QueryBuilder.build_where_conditions("i", conditions)

        # Add pagination parameters
        parameters["limit"] = limit
        parameters["offset"] = offset

        query = f"""
        MATCH (i:Intermediary)
        {where_clause}
        RETURN i
        ORDER BY i.name
        SKIP $offset
        LIMIT $limit
        """

        return query.strip(), parameters

    @staticmethod
    def get_entity_details(
        node_id: str, include_relationships: bool = True
    ) -> tuple[str, Dict[str, Any]]:
        """Build query to get detailed entity information."""
        parameters = {"node_id": node_id}

        if include_relationships:
            query = """
            MATCH (e:Entity {node_id: $node_id})
            OPTIONAL MATCH (e)-[r]-(related)
            RETURN e,
                   collect(DISTINCT {
                       relationship: type(r),
                       direction: CASE
                           WHEN startNode(r) = e THEN 'outgoing'
                           ELSE 'incoming'
                       END,
                       related_node: related,
                       related_labels: labels(related)
                   }) as relationships
            """
        else:
            query = """
            MATCH (e:Entity {node_id: $node_id})
            RETURN e, [] as relationships
            """

        return query.strip(), parameters

    @staticmethod
    def get_connections(
        start_node_id: str,
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 2,
        node_types: Optional[List[str]] = None,
        limit: int = 50,
    ) -> tuple[str, Dict[str, Any]]:
        """Build query to explore connections from a starting node."""
        parameters = {
            "start_node_id": start_node_id,
            "max_depth": max_depth,
            "limit": limit,
        }

        # Build relationship type filter
        rel_filter = ""
        if relationship_types:
            rel_types = "|".join(relationship_types)
            rel_filter = f":{rel_types}"

        # Build node type filter
        node_filter = ""
        if node_types:
            node_conditions = " OR ".join(
                [f"'{nt}' IN labels(connected)" for nt in node_types]
            )
            node_filter = f" AND ({node_conditions})"

        query = f"""
        MATCH (start {{node_id: $start_node_id}})
        MATCH path = (start)-[r{rel_filter}*1..$max_depth]-(connected)
        WHERE connected.node_id <> $start_node_id{node_filter}
        WITH connected, relationships(path) as path_rels, length(path) as distance
        RETURN DISTINCT connected,
               distance,
               path_rels[0] as first_relationship
        ORDER BY distance, connected.name
        LIMIT $limit
        """

        return query.strip(), parameters

    @staticmethod
    def get_statistics(stat_type: str = "overview") -> tuple[str, Dict[str, Any]]:
        """Build query for database statistics."""
        parameters: Dict[str, Any] = {}

        if stat_type == "overview":
            query = """
            CALL {
                MATCH (e:Entity) RETURN count(e) as entity_count
            }
            CALL {
                MATCH (o:Officer) RETURN count(o) as officer_count
            }
            CALL {
                MATCH (i:Intermediary) RETURN count(i) as intermediary_count
            }
            CALL {
                MATCH (a:Address) RETURN count(a) as address_count
            }
            CALL {
                MATCH ()-[r]->() RETURN count(r) as relationship_count
            }
            RETURN entity_count, officer_count, intermediary_count, address_count, relationship_count
            """

        elif stat_type == "by_source":
            query = """
            MATCH (n)
            WHERE n.sourceID IS NOT NULL
            RETURN n.sourceID as source, labels(n)[0] as node_type, count(*) as count
            ORDER BY source, node_type
            """

        elif stat_type == "by_jurisdiction":
            query = """
            MATCH (e:Entity)
            WHERE e.jurisdiction IS NOT NULL
            RETURN e.jurisdiction as jurisdiction,
                   e.jurisdiction_description as description,
                   count(*) as entity_count
            ORDER BY entity_count DESC
            LIMIT 50
            """

        elif stat_type == "relationship_counts":
            query = """
            MATCH ()-[r]->()
            RETURN type(r) as relationship_type, count(*) as count
            ORDER BY count DESC
            """

        else:
            # Default to overview
            query = """
            MATCH (n)
            RETURN labels(n)[0] as node_type, count(*) as count
            ORDER BY count DESC
            """

        return query.strip(), parameters
