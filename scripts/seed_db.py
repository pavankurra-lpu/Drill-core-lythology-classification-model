#!/usr/bin/env python3
"""
=============================================================================
Lithology Classification System - Database Seeder
=============================================================================
Seeds the database with initial users, sample predictions, and analytics data.
Run this after database migrations are complete.

Usage:
    python scripts/seed_db.py
    python scripts/seed_db.py --reset   # Clears existing data first
=============================================================================
"""

import argparse
import asyncio
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
import random

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ---------------------------------------------------------------------------
# Seed Data Constants
# ---------------------------------------------------------------------------

LITHOLOGY_CLASSES = [
    "Sandstone",
    "Shale",
    "Limestone",
    "Granite",
    "Basalt",
    "Quartzite",
    "Mudstone",
    "Dolomite",
    "Conglomerate",
    "Coal",
]

LITHOLOGY_DESCRIPTIONS = {
    "Sandstone": "Clastic sedimentary rock composed mainly of sand-sized minerals or rock grains. Typically quartz or feldspar.",
    "Shale": "Fine-grained sedimentary rock formed from compacted mud or clay. Often fissile and laminated.",
    "Limestone": "Sedimentary rock composed mainly of skeletal fragments of marine organisms such as coral and mollusks.",
    "Granite": "Coarse-grained igneous rock composed of quartz, alkali feldspar, and plagioclase. Intrusive origin.",
    "Basalt": "Fine-grained mafic igneous rock. Most common volcanic rock on Earth's surface.",
    "Quartzite": "Metamorphic rock consisting chiefly of quartz. Formed from sandstone through metamorphism.",
    "Mudstone": "Sedimentary rock composed of clay minerals. Similar to shale but without fissility.",
    "Dolomite": "Carbonate sedimentary rock composed of dolomite mineral CaMg(CO₃)₂.",
    "Conglomerate": "Coarse-grained clastic sedimentary rock composed of rounded gravel-sized clasts.",
    "Coal": "Combustible black sedimentary rock formed from ancient plant material. High carbon content.",
}

GEOLOGICAL_FORMATIONS = [
    "Morrison Formation",
    "Navajo Sandstone",
    "Green River Formation",
    "Chinle Formation",
    "Entrada Sandstone",
    "Permian Basin",
    "Eagle Ford Shale",
    "Bakken Formation",
    "Marcellus Shale",
    "Barnett Shale",
]

SAMPLE_USERS = [
    {
        "email": "admin@lithology.ai",
        "username": "admin",
        "full_name": "System Administrator",
        "password": "Admin@123456",
        "role": "admin",
        "is_active": True,
        "is_verified": True,
        "organization": "Lithology AI Research Lab",
        "bio": "System administrator with full access to all platform features.",
    },
    {
        "email": "demo@lithology.ai",
        "username": "demo_user",
        "full_name": "Demo User",
        "password": "Demo@123456",
        "role": "user",
        "is_active": True,
        "is_verified": True,
        "organization": "Mining Exploration Corp",
        "bio": "Demo account for exploring the lithology classification platform.",
    },
    {
        "email": "geologist@lithology.ai",
        "username": "dr_stone",
        "full_name": "Dr. Sarah Stone",
        "password": "Geologist@123456",
        "role": "user",
        "is_active": True,
        "is_verified": True,
        "organization": "GeoAnalytics International",
        "bio": "Senior geologist specializing in sedimentary basin analysis.",
    },
]

SAMPLE_PREDICTIONS = [
    {
        "filename": "core_sample_001.jpg",
        "predicted_class": "Sandstone",
        "confidence": 0.9234,
        "depth_m": 125.5,
        "formation": "Morrison Formation",
        "drill_site": "Site-Alpha-7",
        "notes": "Fine to medium-grained sandstone with cross-bedding visible.",
        "processing_time_ms": 1234,
        "model_version": "efficientnet_b3_v1.0",
    },
    {
        "filename": "core_sample_002.jpg",
        "predicted_class": "Shale",
        "confidence": 0.8876,
        "depth_m": 230.2,
        "formation": "Eagle Ford Shale",
        "drill_site": "Site-Beta-12",
        "notes": "Dark gray shale with organic material. High TOC potential.",
        "processing_time_ms": 987,
        "model_version": "efficientnet_b3_v1.0",
    },
    {
        "filename": "core_sample_003.jpg",
        "predicted_class": "Limestone",
        "confidence": 0.9541,
        "depth_m": 478.8,
        "formation": "Permian Basin",
        "drill_site": "Site-Gamma-3",
        "notes": "Fossiliferous limestone with abundant brachiopods and crinoids.",
        "processing_time_ms": 1456,
        "model_version": "efficientnet_b3_v1.0",
    },
    {
        "filename": "core_sample_004.jpg",
        "predicted_class": "Granite",
        "confidence": 0.9712,
        "depth_m": 1205.0,
        "formation": "Basement Complex",
        "drill_site": "Site-Delta-1",
        "notes": "Coarse-grained pink granite with K-feldspar megacrysts.",
        "processing_time_ms": 1123,
        "model_version": "efficientnet_b3_v1.0",
    },
    {
        "filename": "core_sample_005.jpg",
        "predicted_class": "Basalt",
        "confidence": 0.8923,
        "depth_m": 650.5,
        "formation": "Columbia River Basalt",
        "drill_site": "Site-Epsilon-9",
        "notes": "Massive dark basalt with vesicles. Minor olivine phenocrysts.",
        "processing_time_ms": 1089,
        "model_version": "efficientnet_b3_v1.0",
    },
    {
        "filename": "core_sample_006.jpg",
        "predicted_class": "Quartzite",
        "confidence": 0.9345,
        "depth_m": 890.3,
        "formation": "Cambrian Quartzite",
        "drill_site": "Site-Zeta-5",
        "notes": "White to light gray quartzite. Very hard and dense.",
        "processing_time_ms": 1345,
        "model_version": "efficientnet_b3_v1.0",
    },
    {
        "filename": "core_sample_007.jpg",
        "predicted_class": "Mudstone",
        "confidence": 0.8234,
        "depth_m": 156.7,
        "formation": "Chinle Formation",
        "drill_site": "Site-Eta-2",
        "notes": "Red-brown mudstone with desiccation cracks.",
        "processing_time_ms": 892,
        "model_version": "efficientnet_b3_v1.0",
    },
    {
        "filename": "core_sample_008.jpg",
        "predicted_class": "Dolomite",
        "confidence": 0.9087,
        "depth_m": 334.1,
        "formation": "Silurian Dolomite",
        "drill_site": "Site-Theta-4",
        "notes": "Cream-colored dolomite with rhombic crystal faces.",
        "processing_time_ms": 1234,
        "model_version": "efficientnet_b3_v1.0",
    },
    {
        "filename": "core_sample_009.jpg",
        "predicted_class": "Conglomerate",
        "confidence": 0.8567,
        "depth_m": 78.5,
        "formation": "Cretaceous Conglomerate",
        "drill_site": "Site-Iota-6",
        "notes": "Poorly sorted conglomerate with rounded chert clasts.",
        "processing_time_ms": 1678,
        "model_version": "efficientnet_b3_v1.0",
    },
    {
        "filename": "core_sample_010.jpg",
        "predicted_class": "Coal",
        "confidence": 0.9456,
        "depth_m": 412.3,
        "formation": "Pennsylvanian Coal Measures",
        "drill_site": "Site-Kappa-8",
        "notes": "Bright banded coal (vitrain, clarain). Bituminous rank.",
        "processing_time_ms": 1098,
        "model_version": "efficientnet_b3_v1.0",
    },
]


async def seed_database(reset: bool = False) -> None:
    """Main seeding function."""
    print("\n" + "=" * 60)
    print("  🪨 Lithology Classification System - Database Seeder")
    print("=" * 60 + "\n")

    try:
        # Try to import app modules
        from app.core.database import AsyncSessionLocal, engine, Base
        from app.core.security import get_password_hash
        from app.models.user import User, UserRole
        from app.models.prediction import Prediction, PredictionStatus
        from sqlalchemy import select, delete

        async with AsyncSessionLocal() as session:
            async with session.begin():

                if reset:
                    print("⚠️  Resetting database...")
                    await session.execute(delete(Prediction))
                    await session.execute(delete(User))
                    print("   ✓ Cleared existing data")

                # ---------------------------------------------------------------
                # Seed Users
                # ---------------------------------------------------------------
                print("👤 Seeding users...")
                created_users = {}

                for user_data in SAMPLE_USERS:
                    # Check if user already exists
                    result = await session.execute(
                        select(User).where(User.email == user_data["email"])
                    )
                    existing = result.scalar_one_or_none()

                    if existing:
                        print(f"   ℹ  User already exists: {user_data['email']}")
                        created_users[user_data["email"]] = existing
                        continue

                    user = User(
                        id=uuid.uuid4(),
                        email=user_data["email"],
                        username=user_data["username"],
                        full_name=user_data["full_name"],
                        hashed_password=get_password_hash(user_data["password"]),
                        role=UserRole[user_data["role"].upper()],
                        is_active=user_data["is_active"],
                        is_verified=user_data["is_verified"],
                        organization=user_data.get("organization"),
                        bio=user_data.get("bio"),
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
                    session.add(user)
                    created_users[user_data["email"]] = user
                    print(f"   ✓ Created user: {user_data['email']} ({user_data['role']})")

                await session.flush()

                # ---------------------------------------------------------------
                # Seed Sample Predictions
                # ---------------------------------------------------------------
                print("\n🔬 Seeding sample predictions...")
                demo_user = created_users.get("demo@lithology.ai")
                admin_user = created_users.get("admin@lithology.ai")

                for i, pred_data in enumerate(SAMPLE_PREDICTIONS):
                    user = demo_user if i % 3 != 0 else admin_user
                    if user is None:
                        continue

                    # Generate realistic class probabilities
                    predicted_idx = LITHOLOGY_CLASSES.index(pred_data["predicted_class"])
                    probs = [random.uniform(0.001, 0.05) for _ in LITHOLOGY_CLASSES]
                    probs[predicted_idx] = pred_data["confidence"]
                    total = sum(probs)
                    probs = [p / total for p in probs]

                    # Stagger creation times over past 30 days
                    created_at = datetime.now(timezone.utc) - timedelta(
                        days=random.randint(0, 30),
                        hours=random.randint(0, 23),
                        minutes=random.randint(0, 59),
                    )

                    prediction = Prediction(
                        id=uuid.uuid4(),
                        user_id=user.id,
                        filename=pred_data["filename"],
                        original_filename=pred_data["filename"],
                        file_path=f"uploads/images/{pred_data['filename']}",
                        file_size=random.randint(500_000, 5_000_000),
                        predicted_class=pred_data["predicted_class"],
                        confidence=pred_data["confidence"],
                        class_probabilities=dict(zip(LITHOLOGY_CLASSES, probs)),
                        depth_m=pred_data.get("depth_m"),
                        formation=pred_data.get("formation"),
                        drill_site=pred_data.get("drill_site"),
                        notes=pred_data.get("notes"),
                        processing_time_ms=pred_data.get("processing_time_ms"),
                        model_version=pred_data.get("model_version", "efficientnet_b3_v1.0"),
                        status=PredictionStatus.COMPLETED,
                        description=LITHOLOGY_DESCRIPTIONS.get(pred_data["predicted_class"], ""),
                        created_at=created_at,
                        updated_at=created_at,
                    )
                    session.add(prediction)
                    print(
                        f"   ✓ Created prediction: {pred_data['filename']} "
                        f"-> {pred_data['predicted_class']} ({pred_data['confidence']:.1%})"
                    )

                print("\n✅ Database seeding completed successfully!")

        # Print summary
        print("\n" + "=" * 60)
        print("  📊 Seeding Summary")
        print("=" * 60)
        print(f"  Users created:       {len(SAMPLE_USERS)}")
        print(f"  Predictions seeded:  {len(SAMPLE_PREDICTIONS)}")
        print("")
        print("  Default Credentials:")
        for u in SAMPLE_USERS:
            print(f"    {u['role']:6s} | {u['email']:30s} | {u['password']}")
        print("")

    except ImportError as e:
        print(f"\n⚠️  App modules not found: {e}")
        print("   Running in standalone mode - printing seed data summary only.")
        print("\n  Users that would be created:")
        for u in SAMPLE_USERS:
            print(f"    - {u['email']} ({u['role']})")
        print(f"\n  Predictions that would be seeded: {len(SAMPLE_PREDICTIONS)}")

    except Exception as e:
        print(f"\n❌ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Seed the Lithology Classification System database"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear existing data before seeding (DESTRUCTIVE!)",
    )
    args = parser.parse_args()

    if args.reset:
        confirm = input(
            "\n⚠️  WARNING: This will delete all existing data! Type 'yes' to confirm: "
        )
        if confirm.lower() != "yes":
            print("Aborted.")
            sys.exit(0)

    asyncio.run(seed_database(reset=args.reset))


if __name__ == "__main__":
    main()
