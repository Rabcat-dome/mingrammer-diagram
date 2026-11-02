"""Stable render diagnostics. Messages never carry labels, host paths or engine output."""

from ..diagnostics import Diagnostic

MESSAGES = {
    "RENDER_VIEW_TOO_LARGE": (
        "The selected view exceeds the render limit on entities or relationships.",
        "Split it into smaller views, such as an overview plus one detail view per area.",
    ),
    "RENDER_GROUP_DEPTH_LIMIT": (
        "The selected view nests groups deeper than the render limit.",
        "Use a grouping with fewer levels, or split the nested part into its own view.",
    ),
    "RENDER_TYPE_BLOCKED": (
        "This type has no usable icon and takes no substitute, so it cannot be drawn.",
        "Resolve the blocker the catalog names, or exclude the type and disclose the exclusion.",
    ),
    "RENDER_TYPE_UNRESOLVED": (
        "A selected entity has no catalog representation to draw.",
        "Use a catalog type; an unknown service type is drawable only in lenient mode.",
    ),
    "RENDER_ASSET_UNSAFE": (
        "A catalog icon or font is unlisted, outside its controlled root or differs from its recorded digest.",
        "Reinstall the package from its lock; never replace the file with another one.",
    ),
    "RENDER_ENGINE_UNAVAILABLE": (
        "Graphviz dot was not found, or its version could not be read.",
        "Install Graphviz, for example with: brew install graphviz.",
    ),
    "RENDER_ISOLATION_UNAVAILABLE": (
        "The sandbox that denies the renderer network access is not available on this host.",
        "Render on a macOS host with sandbox-exec; other hosts are not supported yet.",
    ),
    "RENDER_FONT_UNAVAILABLE": (
        "Graphviz did not use the bundled fonts, so its layout would depend on this host.",
        "Install a Graphviz build with Pango and Fontconfig support, such as Homebrew's.",
    ),
    "RENDER_TIMEOUT": (
        "Graphviz exceeded the render time limit and was stopped.",
        "Split the view into smaller views.",
    ),
    "RENDER_MEMORY_LIMIT": (
        "Graphviz exceeded the render memory limit and was stopped.",
        "Split the view into smaller views.",
    ),
    "RENDER_TEMPORARY_LIMIT": (
        "Graphviz exceeded the temporary storage limit and was stopped.",
        "Split the view into smaller views.",
    ),
    "RENDER_ENGINE_FAILED": (
        "Graphviz could not complete this render.",
        "Check the Graphviz installation, then retry with a smaller view.",
    ),
    "RENDER_OUTPUT_MISSING": (
        "Graphviz finished without producing every requested output file.",
        "Check the Graphviz installation; no bundle was published.",
    ),
    "RENDER_SVG_UNSAFE": (
        "The generated SVG failed its safety check.",
        "No bundle was published. Remove characters XML cannot hold from labels, then retry.",
    ),
    "RENDER_PNG_INVALID": (
        "The generated PNG is not a complete, valid image.",
        "No bundle was published. Check the Graphviz installation, then retry.",
    ),
    "RENDER_PIXEL_LIMIT": (
        "The generated PNG exceeds the pixel limit.",
        "Split the view into smaller views.",
    ),
    "RENDER_ARTIFACT_LIMIT": (
        "A generated file exceeds the artifact size limit.",
        "Split the view into smaller views.",
    ),
    "RENDER_CONTENT_MISSING": (
        "The generated image lost a selected element, icon or label.",
        "No bundle was published. Report this as a renderer defect.",
    ),
    "RENDER_OUTPUT_PATH_UNSAFE": (
        "The output root is not a real, private directory owned by this user.",
        "Pass a directory with no symbolic link in its path, not writable by group or others.",
    ),
    "RENDER_OUTPUT_WRITE_FAILED": (
        "A file could not be written under the output root.",
        "Check free disk space and permissions on the output root, then retry.",
    ),
    "RENDER_OUTPUT_ROOT_CHANGED": (
        "The output root changed during the render.",
        "Keep the output root in place while rendering, then retry.",
    ),
    "RENDER_BUNDLE_COLLISION": (
        "A bundle with this name already exists, so it was not overwritten.",
        "Retry; each render picks a new bundle name.",
    ),
    "RENDER_INTERRUPTED": (
        "The render was interrupted and its temporary files were removed.",
        "Retry the render.",
    ),
    "RENDER_GENERIC_FALLBACK": (
        "An unknown service type is drawn with the approved generic symbol, keeping its provider, type and label.",
        "Use a catalog type before treating this diagram as final; lenient output stays a draft.",
    ),
}
# These describe the request rather than the host, so they exit like an invalid model.
REQUEST_CODES = frozenset(
    {"RENDER_VIEW_TOO_LARGE", "RENDER_GROUP_DEPTH_LIMIT", "RENDER_TYPE_BLOCKED"}
)


def diagnostic(
    code: str,
    field: str = "/render",
    entity_id: str | None = None,
    severity: str = "error",
) -> Diagnostic:
    message, remedy = MESSAGES[code]
    return Diagnostic.model_validate(
        {
            "severity": severity,
            "code": code,
            "field": field,
            "entity_id": entity_id,
            "message": message,
            "remedy": remedy,
        }
    )


class RenderFailure(Exception):
    def __init__(self, code: str, field: str = "/render", entity_id: str | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.field = field
        self.entity_id = entity_id

    def diagnostic(self) -> Diagnostic:
        return diagnostic(self.code, self.field, self.entity_id)
