"""
Recipe: Configuration Database
Database: TinyDB
Description: Demonstrates using TinyDB as a configuration store with table separation.
             Uses separate tables for app settings, user preferences, and feature flags,
             showing how to search by field and organise structured config data.

Usage: python src/recipe_config_database.py
"""

import os
import tempfile

from tinydb import Query, TinyDB


def main() -> None:
    # Use a temporary file so we don't leave artifacts on disk
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    tmp.close()
    db_path = tmp.name

    try:
        db = TinyDB(db_path)

        # --- 1. Create separate tables for different config domains ---
        app_table = db.table("app_settings")
        users_table = db.table("user_preferences")
        flags_table = db.table("feature_flags")

        # --- 2. Populate app settings ---
        app_table.insert_multiple(
            [
                {"key": "log_level", "value": "INFO", "env": "production"},
                {"key": "max_connections", "value": 100, "env": "production"},
                {"key": "timeout_seconds", "value": 30, "env": "production"},
                {"key": "log_level", "value": "DEBUG", "env": "development"},
                {"key": "max_connections", "value": 10, "env": "development"},
            ]
        )

        # --- 3. Populate user preferences ---
        users_table.insert_multiple(
            [
                {"user_id": "u1", "theme": "dark", "language": "en", "notifications": True},
                {"user_id": "u2", "theme": "light", "language": "fr", "notifications": False},
                {"user_id": "u3", "theme": "dark", "language": "en", "notifications": True},
            ]
        )

        # --- 4. Populate feature flags ---
        flags_table.insert_multiple(
            [
                {"flag": "new_dashboard", "enabled": True, "rollout_pct": 50},
                {"flag": "dark_mode", "enabled": True, "rollout_pct": 100},
                {"flag": "beta_search", "enabled": False, "rollout_pct": 0},
            ]
        )

        # --- 5. Search by field ---
        AppSetting = Query()
        UserPref = Query()
        Flag = Query()

        # Query app settings for a specific environment
        prod_settings = app_table.search(AppSetting.env == "production")
        print(f"Production settings ({len(prod_settings)}):")
        for s in prod_settings:
            print(f"  {s['key']} = {s['value']}")

        # Find a specific setting by key and env
        dev_log_level = app_table.get(
            (AppSetting.key == "log_level") & (AppSetting.env == "development")
        )
        print(f"\nDev log level: {dev_log_level}")

        # --- 6. Find users with specific preferences ---
        dark_theme_users = users_table.search(UserPref.theme == "dark")
        print(f"\nUsers with dark theme: {[u['user_id'] for u in dark_theme_users]}")

        # Users with notifications enabled
        notified = users_table.search(UserPref.notifications == True)
        print(f"Users with notifications on: {[u['user_id'] for u in notified]}")

        # --- 7. Check feature flags ---
        # Find all enabled flags
        enabled_flags = flags_table.search(Flag.enabled == True)
        print(f"\nEnabled feature flags: {[f['flag'] for f in enabled_flags]}")

        # Check a specific flag
        beta = flags_table.get(Flag.flag == "beta_search")
        print(f"Beta search enabled: {beta['enabled']}")

        # --- 8. Update a config value ---
        flags_table.update({"enabled": True, "rollout_pct": 10}, Flag.flag == "beta_search")
        updated_beta = flags_table.get(Flag.flag == "beta_search")
        print(f"\nUpdated beta search: enabled={updated_beta['enabled']}, rollout={updated_beta['rollout_pct']}%")

        # --- 9. Show all tables ---
        print(f"\nAll tables: {db.tables()}")

        # --- 10. Show document counts per table ---
        print(f"App settings: {len(app_table)}")
        print(f"User preferences: {len(users_table)}")
        print(f"Feature flags: {len(flags_table)}")

        db.close()

    finally:
        os.unlink(db_path)


if __name__ == "__main__":
    main()
