"""YANG Graph Single Plugin for cross-module list and leafref relationships"""

from __future__ import print_function
import json
import logging
import sys
import re

from pyang import plugin
from pyang import statements
from pyang import error

sys.setrecursionlimit(10000)
logging.basicConfig(level=logging.DEBUG)


class YangGraphSingle(plugin.PyangPlugin):
    def add_output_format(self, fmts):
        fmts["yang-graph-single"] = self

    def setup_ctx(self, ctx):
        ctx.opts.stmts = None
        logging.debug("Context setup complete")

    def setup_fmt(self, ctx):
        ctx.implicit_errors = False
        logging.debug("Format setup complete")

    def emit(self, ctx, modules, fd):
        logging.debug(
            f"Entering emit with {len(modules)} modules: {[m.arg for m in modules]}"
        )
        loaded_modules = [m.arg for m in ctx.modules.values()]
        logging.debug(f"Loaded modules in context: {loaded_modules}")
        if not modules:
            raise error.EmitError("No modules provided to emit.")

        result = {"nodes": [], "edges": []}
        processed_nodes = set()

        for module in modules:
            try:
                logging.debug(f"Processing module: {module.arg}")
                prune_statements(module)
                self._build_graph(module, result, processed_nodes)
            except Exception as e:
                logging.error(
                    f"Error processing module {module.arg}: {e}", exc_info=True
                )
                raise error.EmitError(f"Module processing failed: {e}")

        try:
            json_data = json.dumps(
                result, indent=2, ensure_ascii=False, sort_keys=False
            )
            fd.write(json_data)
            logging.info(f"Output written for {len(modules)} modules")
        except json.JSONDecodeError as e:
            logging.error(f"Error writing JSON: {e}")
            raise

    def _build_graph(self, stmt, result, processed_nodes, module=None):
        if not module:
            module = stmt.i_module

        # Handle lists (only config true for full processing)
        if stmt.keyword == "list" and stmt.i_config:
            list_name = qualify_name(stmt, module)
            if list_name in processed_nodes:
                return
            processed_nodes.add(list_name)

            description = stmt.search_one("description")
            description_str = (
                preprocess_string(description.arg)
                if description
                else "No description available"
            )
            key_stmt = stmt.search_one("key")
            key = key_stmt.arg if key_stmt else None
            node = {
                "id": list_name,
                "type": "list",
                "module": module.arg,
                "description": description_str,
                "key": key,
            }
            result["nodes"].append(node)
            logging.debug(f"Added list node: {list_name}")

        # Process leaf/leaf-list with leafrefs (direct or via typedef)
        if stmt.keyword in ("leaf", "leaf-list"):
            type_stmt = stmt.search_one("type")
            if type_stmt:
                path_stmt = type_stmt.search_one("path")
                resolved_type = type_stmt

                # Resolve typedef if present
                if ":" in type_stmt.arg and not path_stmt:
                    prefix, type_name = type_stmt.arg.split(":", 1)
                    target_module = next(
                        (
                            m
                            for m in module.i_ctx.modules.values()
                            if m.search_one("prefix")
                            and m.search_one("prefix").arg == prefix
                        ),
                        None,
                    )
                    if target_module:
                        typedef = self._find_typedef_by_name(target_module, type_name)
                        if typedef:
                            resolved_type = typedef.search_one("type")
                            path_stmt = (
                                resolved_type.search_one("path")
                                if resolved_type
                                else None
                            )
                            logging.debug(
                                f"Resolved typedef {type_stmt.arg} to {resolved_type.arg if resolved_type else 'no type'}"
                            )

                if path_stmt:  # Leafref detected (direct or via typedef)
                    logging.debug(
                        f"Found leafref: {stmt.arg} with path {path_stmt.arg}"
                    )
                    parent_list = self._find_parent_list(stmt)
                    if parent_list:
                        source_name = qualify_name(parent_list, module)
                        if source_name not in processed_nodes:
                            description = parent_list.search_one("description")
                            description_str = (
                                preprocess_string(description.arg)
                                if description
                                else "No description available"
                            )
                            key_stmt = parent_list.search_one("key")
                            key = key_stmt.arg if key_stmt else None
                            node = {
                                "id": source_name,
                                "type": "list",
                                "module": module.arg,
                                "description": description_str,
                                "key": key,
                            }
                            result["nodes"].append(node)
                            processed_nodes.add(source_name)
                            logging.debug(f"Added source node: {source_name}")

                        # Resolve leafref target
                        target_module, target_list, target_key = (
                            self._resolve_leafref_path(path_stmt.arg, module)
                        )
                        if target_module and target_list:
                            target_full_name = f"{target_module.arg}:{target_list}"
                            if target_full_name not in processed_nodes:
                                target_module_stmt = module.i_ctx.modules.get(
                                    target_module.arg
                                )
                                if target_module_stmt:
                                    target_list_stmt = self._find_stmt_by_name(
                                        target_module_stmt, target_list
                                    )
                                    if target_list_stmt:
                                        description = target_list_stmt.search_one(
                                            "description"
                                        )
                                        description_str = (
                                            preprocess_string(description.arg)
                                            if description
                                            else "No description available"
                                        )
                                        key_stmt = target_list_stmt.search_one("key")
                                        key = key_stmt.arg if key_stmt else None
                                        node = {
                                            "id": target_full_name,
                                            "type": "list",
                                            "module": target_module.arg,
                                            "description": description_str,
                                            "key": key,
                                        }
                                        result["nodes"].append(node)
                                        processed_nodes.add(target_full_name)
                                        logging.debug(
                                            f"Added target node: {target_full_name}"
                                        )
                                    else:
                                        logging.debug(
                                            f"Target list {target_list} not found in {target_module.arg}"
                                        )
                                else:
                                    logging.debug(
                                        f"Target module {target_module.arg} not in context"
                                    )

                            if source_name != target_full_name:
                                edge = {
                                    "source": source_name,
                                    "target": target_full_name,
                                    "relationship": f"leafref:{stmt.arg}",
                                }
                                if edge not in result["edges"]:
                                    result["edges"].append(edge)
                                    logging.debug(
                                        f"Added edge: {source_name} -> {target_full_name}"
                                    )
                        else:
                            logging.debug(
                                f"Failed to resolve leafref path: {path_stmt.arg}"
                            )

        # Process children
        for child in getattr(stmt, "i_children", []):
            self._build_graph(child, result, processed_nodes, module)

    def _find_parent_list(self, stmt):
        """Find the nearest parent list of a statement."""
        current = stmt
        while current and current.keyword != "module":
            if current.keyword == "list":
                return current
            current = current.parent
        return None

    def _find_typedef_by_name(self, module, name):
        """Find a typedef statement by name in the module."""
        if hasattr(module, "i_typedefs") and name in module.i_typedefs:
            return module.i_typedefs[name]
        for stmt in getattr(module, "i_children", []):
            if stmt.keyword == "typedef" and stmt.arg == name:
                return stmt
            found = self._find_typedef_by_name(stmt, name)
            if found:
                return found
        return None

    def _resolve_leafref_path(self, path, source_module):
        """Resolve leafref path to target module, list, and key."""
        parts = path.strip("/").split("/")
        current_module = source_module
        target_list = None
        target_key = None

        logging.debug(f"Resolving path: {path}")
        for i, part in enumerate(parts):
            if not part:
                continue
            if ":" in part:
                prefix, name = part.split(":", 1)
                current_module = next(
                    (
                        m
                        for m in source_module.i_ctx.modules.values()
                        if m.search_one("prefix")
                        and m.search_one("prefix").arg == prefix
                    ),
                    current_module,
                )
                node_name = name.replace("-", "_")
            else:
                node_name = part.replace("-", "_")

            target_stmt = self._find_stmt_by_name(current_module, node_name)
            if target_stmt and target_stmt.keyword == "list":
                target_list = node_name
                key_stmt = target_stmt.search_one("key")
                target_key = key_stmt.arg if key_stmt else None
                break  # Stop at the first list
            # Remove the fallback to set target_list to the last part
            # elif i == len(parts) - 1:
            #     target_list = node_name

        if target_list:
            logging.debug(
                f"Resolved to {current_module.arg}:{target_list}, key={target_key}"
            )
            return current_module, target_list, target_key
        logging.debug(f"Could not resolve path to a list: {path}")
        return current_module, None, None

    def _find_stmt_by_name(self, module, name):
        """Find a statement by name in the module."""
        for stmt in getattr(module, "i_children", []):
            if stmt.arg.replace("-", "_") == name:
                return stmt
            found = self._find_stmt_by_name(stmt, name)
            if found:
                return found
        return None


def prune_statements(stmt):
    """Prunes all statements except those that are config true or contain leafrefs."""
    pruned_children = []
    for child in stmt.i_children:
        if child.keyword in ("notification", "rpc", "augment", "deviation"):
            logging.debug(f"Pruning {child.keyword} statement: {child.arg}")
            continue
        # Check if this is a leaf/leaf-list with a leafref
        is_leafref = (
            child.keyword in ("leaf", "leaf-list")
            and child.search_one("type")
            and child.search_one("type").search_one("path")
        )
        if (
            child.keyword in ("container", "leaf", "leaf-list", "list")
            and not child.i_config
            and not is_leafref  # Preserve leafrefs even if config false
        ):
            logging.debug(f"Pruning config false {child.keyword}: {child.arg}")
            continue
        if hasattr(child, "i_children"):
            prune_statements(child)
        pruned_children.append(child)
    stmt.i_children = pruned_children
    return stmt


def preprocess_string(s):
    return re.sub(r"\s+", " ", s).replace(":", ";")


def qualify_name(stmt, module):
    return f"{module.arg}:{stmt.arg.replace('-', '_')}"


def pyang_plugin_init():
    plugin.register_plugin(YangGraphSingle())
