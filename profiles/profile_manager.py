"""
Profile Manager - Load, save, and manage tube profiles.

Handles the profiles directory structure:
  profiles/
    library/     - Built-in profiles (shipped with workbench)
    custom/      - User-created profiles
"""

from pathlib import Path
from typing import Dict, List, Optional
import json
import shutil

from .tube_profile import TubeProfile


# Default profiles directory (relative to this module)
_MODULE_DIR = Path(__file__).parent
PROFILES_DIR = _MODULE_DIR / "data"
LIBRARY_DIR = PROFILES_DIR / "library"
CUSTOM_DIR = PROFILES_DIR / "custom"


class ProfileManager:
    """
    Manages tube profiles stored in the profiles directory.

    Profiles are stored as JSON files in either:
    - library/: Built-in profiles (read-only in production)
    - custom/: User-created profiles (read-write)
    """

    def __init__(self, profiles_dir: Optional[Path] = None):
        """
        Initialize the profile manager.

        Args:
            profiles_dir: Override the profiles directory.
                         Defaults to the module's data/ directory.
        """
        self.profiles_dir = Path(profiles_dir) if profiles_dir else PROFILES_DIR
        self.library_dir = self.profiles_dir / "library"
        self.custom_dir = self.profiles_dir / "custom"

        # Ensure directories exist
        self.library_dir.mkdir(parents=True, exist_ok=True)
        self.custom_dir.mkdir(parents=True, exist_ok=True)

        # Cache of loaded profiles
        self._cache: Dict[str, TubeProfile] = {}

    def _profile_path(self, name: str, location: str = "custom") -> Path:
        """Get the path for a profile by name."""
        # Sanitize name for filesystem
        safe_name = name.replace("/", "_").replace("\\", "_")
        if not safe_name.endswith(".json"):
            safe_name += ".json"

        if location == "library":
            return self.library_dir / safe_name
        return self.custom_dir / safe_name

    def list_profiles(self, include_library: bool = True) -> List[str]:
        """
        List all available profile names.

        Args:
            include_library: Include built-in library profiles.

        Returns:
            List of profile names (without .json extension).
        """
        names = []

        # Custom profiles
        for path in self.custom_dir.glob("*.json"):
            names.append(path.stem)

        # Library profiles
        if include_library:
            for path in self.library_dir.glob("*.json"):
                name = path.stem
                if name not in names:  # Custom overrides library
                    names.append(name)

        return sorted(names)

    def get_profile(self, name: str) -> Optional[TubeProfile]:
        """
        Load a profile by name.

        Checks custom/ first, then library/.

        Args:
            name: Profile name (with or without .json).

        Returns:
            TubeProfile if found, None otherwise.
        """
        # Check cache first
        if name in self._cache:
            return self._cache[name]

        # Try custom first
        custom_path = self._profile_path(name, "custom")
        if custom_path.exists():
            try:
                profile = TubeProfile.load(custom_path)
                self._cache[name] = profile
                return profile
            except Exception as e:
                print(f"Error loading profile {name}: {e}")
                return None

        # Try library
        library_path = self._profile_path(name, "library")
        if library_path.exists():
            try:
                profile = TubeProfile.load(library_path)
                self._cache[name] = profile
                return profile
            except Exception as e:
                print(f"Error loading profile {name}: {e}")
                return None

        return None

    def save_profile(
        self,
        profile: TubeProfile,
        to_library: bool = False,
        overwrite: bool = True
    ) -> Path:
        """
        Save a profile to disk.

        Args:
            profile: The TubeProfile to save.
            to_library: Save to library/ instead of custom/.
            overwrite: Allow overwriting existing profiles.

        Returns:
            Path to the saved file.

        Raises:
            FileExistsError: If file exists and overwrite=False.
        """
        location = "library" if to_library else "custom"
        path = self._profile_path(profile.name, location)

        if path.exists() and not overwrite:
            raise FileExistsError(f"Profile already exists: {path}")

        profile.save(path)

        # Update cache
        self._cache[profile.name] = profile

        return path

    def delete_profile(self, name: str, from_library: bool = False) -> bool:
        """
        Delete a profile.

        Args:
            name: Profile name.
            from_library: Delete from library/ instead of custom/.

        Returns:
            True if deleted, False if not found.
        """
        location = "library" if from_library else "custom"
        path = self._profile_path(name, location)

        if path.exists():
            path.unlink()
            # Remove from cache
            self._cache.pop(name, None)
            return True

        return False

    def copy_to_custom(self, name: str) -> Optional[TubeProfile]:
        """
        Copy a library profile to custom for editing.

        Args:
            name: Profile name to copy.

        Returns:
            The copied profile, or None if source not found.
        """
        library_path = self._profile_path(name, "library")
        if not library_path.exists():
            return None

        custom_path = self._profile_path(name, "custom")
        shutil.copy(library_path, custom_path)

        # Reload from custom
        self._cache.pop(name, None)
        return self.get_profile(name)

    def import_from_json(self, json_path: Path) -> TubeProfile:
        """
        Import a profile from an external JSON file.

        Args:
            json_path: Path to the JSON file.

        Returns:
            The imported TubeProfile (also saved to custom/).
        """
        profile = TubeProfile.load(json_path)
        self.save_profile(profile)
        return profile

    def get_all_profiles(self, include_library: bool = True) -> Dict[str, TubeProfile]:
        """
        Load all profiles into a dictionary.

        Args:
            include_library: Include built-in library profiles.

        Returns:
            Dict mapping profile names to TubeProfile objects.
        """
        profiles = {}
        for name in self.list_profiles(include_library=include_library):
            profile = self.get_profile(name)
            if profile:
                profiles[name] = profile
        return profiles

    def clear_cache(self):
        """Clear the profile cache."""
        self._cache.clear()


# Singleton instance for convenience
_default_manager: Optional[ProfileManager] = None


def get_profile_manager() -> ProfileManager:
    """Get the default profile manager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = ProfileManager()
    return _default_manager


def list_profiles() -> List[str]:
    """List all available profiles."""
    return get_profile_manager().list_profiles()


def get_profile(name: str) -> Optional[TubeProfile]:
    """Get a profile by name."""
    return get_profile_manager().get_profile(name)


def save_profile(profile: TubeProfile, to_library: bool = False) -> Path:
    """Save a profile."""
    return get_profile_manager().save_profile(profile, to_library=to_library)
