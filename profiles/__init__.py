"""
SteelBox Profiles Module

Tube profile management with DXF import and tolerance handling.

Usage:
    from profiles import get_profile, list_profiles, TubeProfile

    # List available profiles
    names = list_profiles()

    # Load a profile
    profile = get_profile("2x2x0.125_A36")

    # Calculate tab/slot dimensions
    slot_width = profile.calc_slot_width()
    tab_width = profile.calc_tab_width()
"""

from .tube_profile import (
    TubeProfile,
    ProfileGeometry,
    ProfileTolerances,
    ProfileMaterial,
    ProfileMetadata,
    create_square_tube,
)

from .profile_manager import (
    ProfileManager,
    get_profile_manager,
    get_profile,
    list_profiles,
    save_profile,
)

from .dxf_importer import (
    import_dxf_profile,
    extract_geometry_from_dxf,
    detect_dxf_units,
)

from .sketch_generator import (
    create_tube_wire,
    create_tube_face,
    create_tube_solid,
    create_profile_sketch,
    profile_to_part,
)

__all__ = [
    # Core classes
    "TubeProfile",
    "ProfileGeometry",
    "ProfileTolerances",
    "ProfileMaterial",
    "ProfileMetadata",
    # Factory functions
    "create_square_tube",
    # Manager
    "ProfileManager",
    "get_profile_manager",
    "get_profile",
    "list_profiles",
    "save_profile",
    # DXF import
    "import_dxf_profile",
    "extract_geometry_from_dxf",
    "detect_dxf_units",
    # Sketch generation (FreeCAD)
    "create_tube_wire",
    "create_tube_face",
    "create_tube_solid",
    "create_profile_sketch",
    "profile_to_part",
]
