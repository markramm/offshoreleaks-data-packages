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

    @staticmethod
    def find_shortest_paths(
        start_node_id: str,
        end_node_id: str,
        max_depth: int = 6,
        relationship_types: Optional[List[str]] = None,
        limit: int = 10,
    ) -> tuple[str, Dict[str, Any]]:
        """Find shortest paths between two nodes."""
        parameters = {
            "start_node_id": start_node_id,
            "end_node_id": end_node_id,
            "max_depth": max_depth,
            "limit": limit,
        }

        # Build relationship type filter
        rel_filter = ""
        if relationship_types:
            rel_types = "|".join(relationship_types)
            rel_filter = f":{rel_types}"

        query = f"""
        MATCH (start {{node_id: $start_node_id}}), (end {{node_id: $end_node_id}})
        MATCH path = shortestPath((start)-[r{rel_filter}*1..$max_depth]-(end))
        WITH path, relationships(path) as rels, nodes(path) as path_nodes
        RETURN path,
               length(path) as path_length,
               [rel in rels | type(rel)] as relationship_types,
               [node in path_nodes | {{
                   node_id: node.node_id,
                   name: node.name,
                   labels: labels(node)
               }}] as path_nodes
        ORDER BY path_length
        LIMIT $limit
        """

        return query.strip(), parameters

    @staticmethod
    def analyze_network_patterns(
        node_id: str,
        pattern_type: str = "hub",
        max_depth: int = 3,
        min_connections: int = 5,
        limit: int = 20,
    ) -> tuple[str, Dict[str, Any]]:
        """Analyze network patterns around a node."""
        parameters = {
            "node_id": node_id,
            "max_depth": max_depth,
            "min_connections": min_connections,
            "limit": limit,
        }

        if pattern_type == "hub":
            # Find nodes with many connections (potential hubs)
            query = """
            MATCH (center {node_id: $node_id})
            MATCH (center)-[*1..$max_depth]-(connected)
            WITH connected, count(*) as connection_count
            WHERE connection_count >= $min_connections
            MATCH (connected)-[r]-(neighbor)
            RETURN connected,
                   connection_count,
                   count(DISTINCT neighbor) as total_neighbors,
                   collect(DISTINCT type(r)) as relationship_types,
                   collect(DISTINCT labels(neighbor)[0]) as neighbor_types
            ORDER BY connection_count DESC
            LIMIT $limit
            """

        elif pattern_type == "bridge":
            # Find nodes that bridge different communities
            query = """
            MATCH (center {node_id: $node_id})
            MATCH path = (center)-[*1..$max_depth]-(bridge)-[*1..2]-(community)
            WHERE bridge.node_id <> center.node_id
            WITH bridge, count(DISTINCT community) as communities_connected
            WHERE communities_connected >= $min_connections
            MATCH (bridge)-[r]-(neighbor)
            RETURN bridge,
                   communities_connected,
                   count(DISTINCT neighbor) as total_connections,
                   collect(DISTINCT type(r)) as relationship_types
            ORDER BY communities_connected DESC
            LIMIT $limit
            """

        elif pattern_type == "cluster":
            # Find tightly connected clusters
            query = """
            MATCH (center {node_id: $node_id})
            MATCH (center)-[*1..$max_depth]-(node1)-[r1]-(node2)-[r2]-(node3)
            WHERE node1.node_id <> center.node_id
              AND node2.node_id <> center.node_id
              AND node3.node_id <> center.node_id
              AND node1.node_id <> node3.node_id
            WITH node1, node2, node3, count(*) as cluster_strength
            WHERE cluster_strength >= $min_connections
            RETURN [node1, node2, node3] as cluster_nodes,
                   cluster_strength,
                   [labels(node1)[0], labels(node2)[0], labels(node3)[0]] as node_types
            ORDER BY cluster_strength DESC
            LIMIT $limit
            """

        else:
            # Default: general connectivity analysis
            query = """
            MATCH (center {node_id: $node_id})
            MATCH (center)-[r*1..$max_depth]-(connected)
            WITH connected, length(r) as distance, count(*) as paths_count
            WHERE paths_count >= $min_connections
            RETURN connected,
                   distance,
                   paths_count,
                   labels(connected) as node_types
            ORDER BY paths_count DESC, distance ASC
            LIMIT $limit
            """

        return query.strip(), parameters

    @staticmethod
    def find_common_connections(
        node_ids: List[str],
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 2,
        limit: int = 20,
    ) -> tuple[str, Dict[str, Any]]:
        """Find common connections between multiple nodes."""
        if len(node_ids) < 2:
            raise ValueError("At least 2 node IDs required for common connections")

        parameters = {
            "node_ids": node_ids,
            "max_depth": max_depth,
            "limit": limit,
            "min_connections": len(node_ids),
        }

        # Build relationship type filter
        rel_filter = ""
        if relationship_types:
            rel_types = "|".join(relationship_types)
            rel_filter = f":{rel_types}"

        query = f"""
        UNWIND $node_ids as node_id
        MATCH (source {{node_id: node_id}})
        MATCH (source)-[r{rel_filter}*1..$max_depth]-(common)
        WHERE common.node_id NOT IN $node_ids
        WITH common, collect(DISTINCT source.node_id) as connected_sources
        WHERE size(connected_sources) >= $min_connections
        MATCH (common)-[rel]-(neighbor)
        RETURN common,
               connected_sources,
               size(connected_sources) as connection_count,
               count(DISTINCT neighbor) as total_neighbors,
               collect(DISTINCT type(rel)) as relationship_types
        ORDER BY connection_count DESC, total_neighbors DESC
        LIMIT $limit
        """

        return query.strip(), parameters

    @staticmethod
    def temporal_analysis(
        node_id: str,
        date_field: str = "incorporation_date",
        time_window_days: int = 365,
        limit: int = 50,
    ) -> tuple[str, Dict[str, Any]]:
        """Analyze temporal patterns in entity creation."""
        parameters = {
            "node_id": node_id,
            "time_window_days": time_window_days,
            "limit": limit,
        }

        query = f"""
        MATCH (center {{node_id: $node_id}})
        WHERE center.{date_field} IS NOT NULL
        WITH center, date(center.{date_field}) as center_date
        MATCH (center)-[*1..3]-(related)
        WHERE related.{date_field} IS NOT NULL
        WITH center, center_date, related,
             date(related.{date_field}) as related_date,
             duration.between(date(center.{date_field}), date(related.{date_field})).days as day_diff
        WHERE abs(day_diff) <= $time_window_days
        RETURN related,
               related_date,
               day_diff,
               labels(related) as node_types,
               CASE
                   WHEN day_diff < 0 THEN 'before'
                   WHEN day_diff > 0 THEN 'after'
                   ELSE 'same_day'
               END as temporal_relationship
        ORDER BY abs(day_diff), related.name
        LIMIT $limit
        """

        return query.strip(), parameters

    @staticmethod
    def compliance_risk_analysis(
        node_id: str,
        risk_jurisdictions: Optional[List[str]] = None,
        max_depth: int = 3,
        limit: int = 30,
    ) -> tuple[str, Dict[str, Any]]:
        """Analyze compliance risks in entity networks."""
        parameters = {
            "node_id": node_id,
            "max_depth": max_depth,
            "limit": limit,
        }

        # Default high-risk jurisdictions (can be customized)
        if risk_jurisdictions is None:
            risk_jurisdictions = [
                "British Virgin Islands",
                "Cayman Islands",
                "Panama",
                "Seychelles",
                "Bahamas",
                "Bermuda",
            ]
        parameters["risk_jurisdictions"] = risk_jurisdictions

        query = """
        MATCH (center {node_id: $node_id})
        MATCH path = (center)-[*1..$max_depth]-(risky)
        WHERE risky.jurisdiction IN $risk_jurisdictions
           OR risky.country_codes IN $risk_jurisdictions
           OR risky.countries IN $risk_jurisdictions
        WITH risky, length(path) as distance,
             CASE
                 WHEN risky.status = 'Active' THEN 'high'
                 WHEN risky.status = 'Inactive' THEN 'medium'
                 ELSE 'low'
             END as risk_level
        MATCH (risky)-[r]-(connected)
        RETURN risky,
               distance,
               risk_level,
               risky.jurisdiction as jurisdiction,
               count(DISTINCT connected) as connection_count,
               collect(DISTINCT type(r)) as relationship_types,
               collect(DISTINCT labels(connected)[0]) as connected_types
        ORDER BY
            CASE risk_level
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                ELSE 3
            END,
            distance,
            connection_count DESC
        LIMIT $limit
        """

        return query.strip(), parameters
