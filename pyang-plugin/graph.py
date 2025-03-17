"""YANG Graph Single Plugin for per-module list-to-list relationships"""

from __future__ import print_function
import json
import optparse
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

    def add_opts(self, optparser):
        optlist = [
            optparse.make_option(
                "--config-only",
                action="store_true",
                dest="config_only",
                help="Only include config true statements in the graph.",
            ),
        ]
        group = optparser.add_option_group("YangGraphSingle options")
        group.add_options(optlist)

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
        if not modules:
            raise error.EmitError("No modules provided to emit.")
        if len(modules) > 1:
            logging.warning("Multiple modules provided; using only the first one")

        module = modules[0]
        result = {"nodes": [], "edges": []}

        try:
            logging.debug(f"Processing module: {module.arg}")
            prune_statements(module)  # Call prune_statements here
            self._build_graph(module, result, ctx.opts.config_only)
        except Exception as e:
            logging.error(f"Error processing module {module.arg}: {e}", exc_info=True)
            raise error.EmitError(f"Module processing failed: {e}")

        try:
            json_data = json.dumps(
                result, indent=2, ensure_ascii=False, sort_keys=False
            )
            fd.write(json_data)
            logging.info(f"Output written for {module.arg}")
        except json.JSONDecodeError as e:
            logging.error(f"Error writing JSON: {e}")
            raise

    def _build_graph(self, stmt, result, config_only, module=None):
        if not module:
            module = stmt.i_module
        if (
            config_only
            and stmt.keyword in ("container", "leaf", "leaf-list", "list")
            and not stmt.i_config
        ):
            return

        if stmt.keyword == "list":
            list_name = qualify_name(stmt, module)
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
            logging.debug(f"Added node: {list_name}")

            for child in stmt.i_children:
                if child.keyword == "leaf":
                    type_stmt = child.search_one("type")
                    if type_stmt and type_stmt.arg == "leafref":
                        path_stmt = type_stmt.search_one("path")
                        if path_stmt:
                            logging.debug(
                                f"Found leafref in {list_name}: {path_stmt.arg}"
                            )
                            try:
                                target_module, target_list, target_key = (
                                    self._resolve_leafref_path(path_stmt.arg, module)
                                )
                                if target_list and target_key:
                                    target_full_name = (
                                        f"{target_module.arg}:{target_list}"
                                    )
                                    if list_name != target_full_name:
                                        edge = {
                                            "source": list_name,  # Fully qualified source
                                            "target": target_full_name,  # Fully qualified target
                                            "relationship": f"references_key:{target_key}",
                                        }
                                        result["edges"].append(edge)
                                        logging.debug(
                                            f"Added potential edge: {list_name} -> {target_full_name}"
                                        )
                                    else:
                                        logging.debug(
                                            f"Skipped self-reference: {list_name}"
                                        )
                                else:
                                    logging.debug(
                                        f"Leafref {path_stmt.arg} resolved to no valid target"
                                    )
                            except Exception as e:
                                logging.warning(
                                    f"Failed to resolve leafref {path_stmt.arg}: {e}"
                                )

        for child in getattr(stmt, "i_children", []):
            self._build_graph(child, result, config_only, module)

    def _resolve_leafref_path(self, path, source_module):
        parts = path.strip("/").split("/")
        target_module = source_module
        target_list = None
        target_key = None

        logging.debug(f"Resolving path: {path}")
        for i, part in enumerate(parts):
            if ":" in part:
                prefix, name = part.split(":", 1)
                target_module = next(
                    (
                        m
                        for m in source_module.i_ctx.modules.values()
                        if m.search_one("prefix")
                        and m.search_one("prefix").arg == prefix
                    ),
                    source_module,
                )
                logging.debug(f"Prefix {prefix} resolved to module {target_module.arg}")
                if i == len(parts) - 1:
                    target_key = name.replace("-", "_")
                elif i == len(parts) - 2:
                    target_list = name.replace("-", "_")
            elif part:
                if i == len(parts) - 1:
                    target_key = part.replace("-", "_")
                elif i == len(parts) - 2:
                    target_list = part.replace("-", "_")

        if target_module and target_list and target_key:
            logging.debug(
                f"Potential target: {target_module.arg}:{target_list} with key {target_key}"
            )
            return target_module, target_list, target_key
        logging.debug(
            f"Path resolution incomplete: module={target_module.arg if target_module else None}, list={target_list}, key={target_key}"
        )
        return target_module, None, None


def prune_statements(stmt):
    """Prunes all statements except those that are config true."""
    pruned_children = []
    for child in stmt.i_children:
        if child.keyword in ("notification", "rpc", "augment", "deviation"):
            logging.debug(f"Pruning {child.keyword} statement: {child.arg}")
            continue
        if (
            child.keyword in ("container", "leaf", "leaf-list", "list")
            and not child.i_config
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
