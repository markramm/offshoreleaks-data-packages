"""Data export utilities for investigation results."""

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


@dataclass
class ExportConfig:
    """Configuration for data export."""

    include_metadata: bool = True
    timestamp_format: str = "%Y-%m-%d_%H-%M-%S"
    max_results: Optional[int] = None
    flatten_nested: bool = True


class DataExporter:
    """Export investigation results to various formats."""

    def __init__(self, config: Optional[ExportConfig] = None):
        """Initialize exporter with configuration."""
        self.config = config or ExportConfig()

    def export_to_json(
        self,
        data: Dict[str, Any],
        filename: Optional[str] = None,
        output_dir: str = "exports",
    ) -> str:
        """Export data to JSON format."""
        if filename is None:
            timestamp = datetime.now().strftime(self.config.timestamp_format)
            filename = f"offshore_leaks_export_{timestamp}.json"

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        export_data = self._prepare_export_data(data)

        file_path = output_path / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

        return str(file_path)

    def export_to_csv(
        self,
        data: Dict[str, Any],
        filename: Optional[str] = None,
        output_dir: str = "exports",
    ) -> str:
        """Export data to CSV format."""
        if filename is None:
            timestamp = datetime.now().strftime(self.config.timestamp_format)
            filename = f"offshore_leaks_export_{timestamp}.csv"

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Flatten data for CSV export
        flattened_data = self._flatten_for_csv(data)

        file_path = output_path / filename
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            if flattened_data:
                writer = csv.DictWriter(f, fieldnames=flattened_data[0].keys())
                writer.writeheader()
                writer.writerows(flattened_data)

        return str(file_path)

    def export_to_excel(
        self,
        data: Dict[str, Any],
        filename: Optional[str] = None,
        output_dir: str = "exports",
    ) -> str:
        """Export data to Excel format (requires pandas)."""
        if not PANDAS_AVAILABLE:
            raise ImportError(
                "pandas is required for Excel export. Install with: pip install pandas openpyxl"
            )

        if filename is None:
            timestamp = datetime.now().strftime(self.config.timestamp_format)
            filename = f"offshore_leaks_export_{timestamp}.xlsx"

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        file_path = output_path / filename

        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            # Export main results
            if "results" in data:
                df_results = pd.DataFrame(self._flatten_for_csv(data))
                df_results.to_excel(writer, sheet_name="Results", index=False)

            # Export metadata
            if self.config.include_metadata and "metadata" in data:
                metadata_rows = []
                for key, value in data["metadata"].items():
                    metadata_rows.append({"Property": key, "Value": str(value)})

                df_metadata = pd.DataFrame(metadata_rows)
                df_metadata.to_excel(writer, sheet_name="Metadata", index=False)

            # Export statistics if available
            if "statistics" in data:
                stats_data = self._flatten_statistics(data["statistics"])
                df_stats = pd.DataFrame(stats_data)
                df_stats.to_excel(writer, sheet_name="Statistics", index=False)

        return str(file_path)

    def export_network_data(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        filename: Optional[str] = None,
        output_dir: str = "exports",
        format: str = "json",
    ) -> str:
        """Export network data in format suitable for visualization tools."""
        if filename is None:
            timestamp = datetime.now().strftime(self.config.timestamp_format)
            filename = f"network_data_{timestamp}.{format}"

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        network_data = {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "node_count": len(nodes),
                "edge_count": len(edges),
                "format_version": "1.0",
            },
        }

        file_path = output_path / filename

        if format.lower() == "json":
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(network_data, f, indent=2, ensure_ascii=False, default=str)
        elif format.lower() == "gexf":
            self._export_to_gexf(network_data, file_path)
        elif format.lower() == "graphml":
            self._export_to_graphml(network_data, file_path)
        else:
            raise ValueError(f"Unsupported network format: {format}")

        return str(file_path)

    def create_investigation_report(
        self,
        investigation_data: Dict[str, Any],
        filename: Optional[str] = None,
        output_dir: str = "exports",
    ) -> str:
        """Create a comprehensive investigation report."""
        if filename is None:
            timestamp = datetime.now().strftime(self.config.timestamp_format)
            filename = f"investigation_report_{timestamp}.json"

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        report = {
            "investigation_metadata": {
                "export_date": datetime.now().isoformat(),
                "report_version": "1.0",
                "tools_used": investigation_data.get("tools_used", []),
                "query_count": investigation_data.get("query_count", 0),
                "total_results": investigation_data.get("total_results", 0),
            },
            "executive_summary": investigation_data.get("summary", {}),
            "detailed_findings": investigation_data.get("findings", {}),
            "risk_assessment": investigation_data.get("risks", {}),
            "network_analysis": investigation_data.get("network_data", {}),
            "supporting_data": investigation_data.get("raw_data", {}),
            "recommendations": investigation_data.get("recommendations", []),
        }

        file_path = output_path / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        return str(file_path)

    def _prepare_export_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for export with metadata."""
        export_data = data.copy()

        if self.config.include_metadata:
            export_data["export_metadata"] = {
                "export_date": datetime.now().isoformat(),
                "exporter_version": "1.0",
                "total_records": len(data.get("results", [])),
                "query_time_ms": data.get("query_time_ms"),
                "offset": data.get("offset"),
                "limit": data.get("limit"),
            }

        # Apply result limit if configured
        if self.config.max_results and "results" in export_data:
            export_data["results"] = export_data["results"][: self.config.max_results]
            if self.config.include_metadata:
                export_data["export_metadata"]["limited_results"] = True
                export_data["export_metadata"]["max_results"] = self.config.max_results

        return export_data

    def _flatten_for_csv(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Flatten nested data structures for CSV export."""
        if "results" not in data:
            return []

        flattened = []
        for result in data["results"]:
            flat_result = self._flatten_dict(result)
            flattened.append(flat_result)

        return flattened

    def _flatten_dict(
        self, d: Dict[str, Any], parent_key: str = "", sep: str = "_"
    ) -> Dict[str, Any]:
        """Recursively flatten a nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k

            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                if v and isinstance(v[0], dict):
                    # For list of dicts, create separate columns
                    for i, item in enumerate(v[:3]):  # Limit to first 3 items
                        if isinstance(item, dict):
                            items.extend(
                                self._flatten_dict(
                                    item, f"{new_key}_{i}", sep=sep
                                ).items()
                            )
                        else:
                            items.append((f"{new_key}_{i}", str(item)))
                else:
                    # For simple lists, join as string
                    items.append((new_key, ", ".join(map(str, v))))
            else:
                items.append((new_key, v))

        return dict(items)

    def _flatten_statistics(self, stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Flatten statistics data for export."""
        flattened = []
        for category, data in stats.items():
            if isinstance(data, list):
                for item in data:
                    row = {"category": category}
                    row.update(self._flatten_dict(item))
                    flattened.append(row)
            elif isinstance(data, dict):
                row = {"category": category}
                row.update(self._flatten_dict(data))
                flattened.append(row)
            else:
                flattened.append({"category": category, "value": data})

        return flattened

    def _export_to_gexf(self, network_data: Dict[str, Any], file_path: Path) -> None:
        """Export network data to GEXF format for Gephi."""
        # Basic GEXF implementation
        gexf_content = """<?xml version="1.0" encoding="UTF-8"?>
<gexf xmlns="http://www.gexf.net/1.2draft" version="1.2">
    <meta lastmodifieddate="{date}">
        <creator>Offshore Leaks MCP Server</creator>
        <description>Network export from offshore leaks database</description>
    </meta>
    <graph mode="static" defaultedgetype="undirected">
        <nodes>
{nodes}
        </nodes>
        <edges>
{edges}
        </edges>
    </graph>
</gexf>"""

        nodes_xml = ""
        for i, node in enumerate(network_data["nodes"]):
            node_id = node.get("node_id", f"node_{i}")
            label = node.get("name", "Unknown")
            nodes_xml += f'            <node id="{node_id}" label="{label}"/>\n'

        edges_xml = ""
        for i, edge in enumerate(network_data["edges"]):
            source = edge.get("source", "")
            target = edge.get("target", "")
            edge_type = edge.get("type", "connected_to")
            edges_xml += f'            <edge id="{i}" source="{source}" target="{target}" label="{edge_type}"/>\n'

        final_content = gexf_content.format(
            date=datetime.now().isoformat(),
            nodes=nodes_xml.rstrip(),
            edges=edges_xml.rstrip(),
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(final_content)

    def _export_to_graphml(self, network_data: Dict[str, Any], file_path: Path) -> None:
        """Export network data to GraphML format."""
        # Basic GraphML implementation
        graphml_content = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns
         http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
    <key id="name" for="node" attr.name="name" attr.type="string"/>
    <key id="type" for="node" attr.name="type" attr.type="string"/>
    <key id="relationship" for="edge" attr.name="relationship" attr.type="string"/>
    <graph id="G" edgedefault="undirected">
{nodes}
{edges}
    </graph>
</graphml>"""

        nodes_xml = ""
        for node in network_data["nodes"]:
            node_id = node.get("node_id", "unknown")
            name = node.get("name", "Unknown")
            node_type = node.get("type", "Entity")
            nodes_xml += f"""        <node id="{node_id}">
            <data key="name">{name}</data>
            <data key="type">{node_type}</data>
        </node>
"""

        edges_xml = ""
        for i, edge in enumerate(network_data["edges"]):
            source = edge.get("source", "")
            target = edge.get("target", "")
            relationship = edge.get("type", "connected_to")
            edges_xml += f"""        <edge id="e{i}" source="{source}" target="{target}">
            <data key="relationship">{relationship}</data>
        </edge>
"""

        final_content = graphml_content.format(
            nodes=nodes_xml.rstrip(), edges=edges_xml.rstrip()
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(final_content)


class NetworkVisualizer:
    """Create network visualizations from offshore leaks data."""

    def __init__(self):
        """Initialize the visualizer."""
        pass

    def prepare_network_data(
        self, connections_result: Dict[str, Any], include_attributes: bool = True
    ) -> Dict[str, Any]:
        """Prepare network data from connections query result."""
        nodes = []
        edges = []
        node_ids = set()

        if "results" not in connections_result:
            return {"nodes": nodes, "edges": edges}

        # Process connections to extract nodes and edges
        for connection in connections_result["results"]:
            if "node" in connection:
                node = connection["node"]
                node_id = node.get("node_id")

                if node_id and node_id not in node_ids:
                    node_data = {
                        "id": node_id,
                        "node_id": node_id,
                        "name": node.get("name", "Unknown"),
                        "type": self._get_node_type(node),
                    }

                    if include_attributes:
                        node_data.update(
                            {
                                "jurisdiction": node.get("jurisdiction"),
                                "status": node.get("status"),
                                "distance": connection.get("distance", 0),
                            }
                        )

                    nodes.append(node_data)
                    node_ids.add(node_id)

        return {"nodes": nodes, "edges": edges}

    def create_d3_visualization_data(
        self, network_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create data structure optimized for D3.js visualization."""
        # Convert to D3 format with numeric indices
        nodes = network_data.get("nodes", [])
        edges = network_data.get("edges", [])

        # Create node lookup
        node_lookup = {node["id"]: i for i, node in enumerate(nodes)}

        # Convert edges to use indices
        d3_edges = []
        for edge in edges:
            source_id = edge.get("source")
            target_id = edge.get("target")

            if source_id in node_lookup and target_id in node_lookup:
                d3_edges.append(
                    {
                        "source": node_lookup[source_id],
                        "target": node_lookup[target_id],
                        "type": edge.get("type", "connected_to"),
                        "weight": edge.get("weight", 1),
                    }
                )

        return {
            "nodes": nodes,
            "links": d3_edges,
            "metadata": {
                "node_count": len(nodes),
                "edge_count": len(d3_edges),
                "visualization_format": "d3",
            },
        }

    def _get_node_type(self, node: Dict[str, Any]) -> str:
        """Determine node type from node data."""
        # Simple heuristic based on available fields
        if "jurisdiction" in node:
            return "Entity"
        elif "countries" in node:
            if "address" in node:
                return "Address"
            else:
                return "Officer"
        else:
            return "Unknown"


# Convenience functions for common export operations
def export_search_results(
    results: Dict[str, Any],
    format: str = "json",
    filename: Optional[str] = None,
    output_dir: str = "exports",
) -> str:
    """Export search results to specified format."""
    exporter = DataExporter()

    if format.lower() == "json":
        return exporter.export_to_json(results, filename, output_dir)
    elif format.lower() == "csv":
        return exporter.export_to_csv(results, filename, output_dir)
    elif format.lower() == "excel":
        return exporter.export_to_excel(results, filename, output_dir)
    else:
        raise ValueError(f"Unsupported format: {format}")


def export_network_for_visualization(
    connections_data: Dict[str, Any],
    format: str = "json",
    filename: Optional[str] = None,
    output_dir: str = "exports",
) -> str:
    """Export network data optimized for visualization tools."""
    visualizer = NetworkVisualizer()
    exporter = DataExporter()

    # Prepare network data
    network_data = visualizer.prepare_network_data(connections_data)

    if format.lower() == "d3":
        d3_data = visualizer.create_d3_visualization_data(network_data)
        return exporter.export_to_json(d3_data, filename, output_dir)
    else:
        return exporter.export_network_data(
            network_data["nodes"], network_data["edges"], filename, output_dir, format
        )
