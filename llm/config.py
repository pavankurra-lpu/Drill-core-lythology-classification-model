"""
llm/config.py
Configuration for LLM and geological knowledge base used as fallback.
"""

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# LLM Configuration
# ---------------------------------------------------------------------------

@dataclass
class LLMConfig:
    """Central configuration for the geological LLM assistant."""

    # HuggingFace model (small enough to run on CPU)
    model_name: str = "google/flan-t5-base"
    tokenizer_name: str = "google/flan-t5-base"

    # Generation parameters
    max_new_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    repetition_penalty: float = 1.1
    do_sample: bool = True

    # Embedding model for RAG / semantic search
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # FAISS index storage
    index_path: str = "data/faiss_index"
    index_file: str = "geological_knowledge.index"
    metadata_file: str = "geological_knowledge_metadata.pkl"

    # Chunking for PDF ingestion
    chunk_size: int = 512
    chunk_overlap: int = 64

    # Device
    device: str = "cpu"

    # Logging
    log_level: str = "INFO"


# ---------------------------------------------------------------------------
# Geological Knowledge Base (fallback when no LLM is available)
# ---------------------------------------------------------------------------

GEOLOGICAL_KNOWLEDGE: dict = {

    # -----------------------------------------------------------------------
    # LITHOLOGY TYPES
    # -----------------------------------------------------------------------
    "lithology": {

        "Granite": {
            "type": "igneous",
            "subtype": "intrusive / plutonic",
            "color": "light gray, pink, or white",
            "texture": "coarse-grained (phaneritic)",
            "hardness": "6–7 Mohs",
            "formation": (
                "Forms from slow cooling of magma deep within the Earth's crust. "
                "The slow cooling allows large mineral crystals to develop."
            ),
            "minerals": ["Quartz", "Feldspar", "Mica", "Amphibole", "Biotite"],
            "characteristics": (
                "Coarse-grained texture with visible interlocking crystals. "
                "Typically light-colored with a speckled appearance. "
                "Very hard and durable."
            ),
            "economic_importance": (
                "Widely used as a construction material, dimension stone, countertops, "
                "and monuments. Source of crushed stone aggregate."
            ),
            "geological_setting": (
                "Found in the cores of mountain ranges, shield areas, and "
                "continental cratons. Associated with batholiths and stocks."
            ),
        },

        "Basalt": {
            "type": "igneous",
            "subtype": "extrusive / volcanic",
            "color": "dark gray to black",
            "texture": "fine-grained (aphanitic) or vesicular",
            "hardness": "5–6 Mohs",
            "formation": (
                "Forms from rapid cooling of mafic lava at or near the Earth's surface. "
                "Common at mid-ocean ridges and hot spots."
            ),
            "minerals": ["Pyroxene", "Olivine", "Feldspar", "Magnetite"],
            "characteristics": (
                "Very fine-grained, dark-colored rock. May contain vesicles (gas bubbles). "
                "Dense and heavy relative to its volume."
            ),
            "economic_importance": (
                "Used as road aggregate, railroad ballast, and building stone. "
                "Basalt fiber used in composites. Important for geothermal energy."
            ),
            "geological_setting": (
                "Most abundant rock on the ocean floor. Found in volcanic island chains, "
                "continental flood basalt provinces, and rift zones."
            ),
        },

        "Sandstone": {
            "type": "sedimentary",
            "subtype": "clastic",
            "color": "tan, brown, yellow, red, or gray",
            "texture": "medium-grained (0.0625–2 mm grain size)",
            "hardness": "6–7 Mohs (varies with cement)",
            "formation": (
                "Forms from compaction and cementation of sand-sized grains "
                "in depositional environments such as rivers, beaches, and deserts."
            ),
            "minerals": ["Quartz", "Feldspar", "Mica", "Clay minerals"],
            "characteristics": (
                "Visible sand grains, often with cross-bedding or ripple marks. "
                "Porosity varies widely. May feel gritty to the touch."
            ),
            "economic_importance": (
                "Major reservoir rock for oil, gas, and groundwater. "
                "Used as building stone, in glass making, and as abrasive."
            ),
            "geological_setting": (
                "River deltas, beaches, dunes, submarine fans, and turbidites. "
                "Common in sedimentary basin sequences."
            ),
        },

        "Limestone": {
            "type": "sedimentary",
            "subtype": "carbonate / chemical / biogenic",
            "color": "white, gray, cream, or tan",
            "texture": "fine to coarse-grained, often with fossils",
            "hardness": "3 Mohs",
            "formation": (
                "Forms from accumulation of calcium carbonate from shells, "
                "coral, and other marine organisms, or from chemical precipitation."
            ),
            "minerals": ["Calcite", "Dolomite", "Clay minerals"],
            "characteristics": (
                "Effervesces with dilute hydrochloric acid. Often contains fossils. "
                "Can be fine-grained (micrite) or coarse-grained (grainstone)."
            ),
            "economic_importance": (
                "Cement production, aggregate, agricultural lime, building stone, "
                "and dimension stone. Important host rock for mineral deposits."
            ),
            "geological_setting": (
                "Warm, shallow marine environments, reefs, lagoons, and "
                "carbonate platforms."
            ),
        },

        "Shale": {
            "type": "sedimentary",
            "subtype": "clastic (fine-grained)",
            "color": "gray, black, brown, or green",
            "texture": "very fine-grained (clay-sized particles)",
            "hardness": "2–3 Mohs",
            "formation": (
                "Forms from compaction of clay, silt, and organic material in "
                "low-energy environments such as deep marine basins and swamps."
            ),
            "minerals": ["Clay minerals", "Quartz", "Feldspar", "Mica", "Pyrite"],
            "characteristics": (
                "Fissile (splits along bedding planes). Very fine-grained, "
                "often with a dull luster. May be organic-rich (black shale)."
            ),
            "economic_importance": (
                "Source rock for hydrocarbons. Shale gas and oil shale are major "
                "energy resources. Used in brick and tile manufacture."
            ),
            "geological_setting": (
                "Deep marine basins, lakes, deltas, and floodplains. "
                "Often interbedded with sandstone and limestone."
            ),
        },

        "Quartzite": {
            "type": "metamorphic",
            "subtype": "non-foliated",
            "color": "white, gray, or pink",
            "texture": "granoblastic (interlocking quartz grains)",
            "hardness": "7 Mohs",
            "formation": (
                "Forms from metamorphism of quartz-rich sandstone under high "
                "temperature and pressure, causing grains to fuse together."
            ),
            "minerals": ["Quartz", "Feldspar", "Mica"],
            "characteristics": (
                "Very hard, dense, and resistant to weathering. "
                "Fractures through grains rather than around them. "
                "Often has a vitreous luster."
            ),
            "economic_importance": (
                "Used as a construction material, road aggregate, railway ballast, "
                "and in silicon production. Resistant to chemical weathering."
            ),
            "geological_setting": (
                "Found in metamorphic terrains, often associated with schists "
                "and gneisses in orogenic belts."
            ),
        },

        "Marble": {
            "type": "metamorphic",
            "subtype": "non-foliated",
            "color": "white, gray, pink, black, or multicolored",
            "texture": "coarse-grained, interlocking calcite or dolomite crystals",
            "hardness": "3 Mohs",
            "formation": (
                "Forms from metamorphism of limestone or dolostone. "
                "Heat and pressure recrystallize calcite into larger grains."
            ),
            "minerals": ["Calcite", "Dolomite", "Tremolite", "Serpentine"],
            "characteristics": (
                "Effervesces with acid. Smooth, crystalline texture. "
                "Can be polished to a high luster. May have foliation."
            ),
            "economic_importance": (
                "Prized as a dimension stone, sculpture medium, and floor covering. "
                "Used in architecture and art throughout history."
            ),
            "geological_setting": (
                "Found in regional and contact metamorphic zones adjacent "
                "to limestone formations."
            ),
        },

        "Slate": {
            "type": "metamorphic",
            "subtype": "foliated (low-grade)",
            "color": "dark gray, black, green, or red",
            "texture": "very fine-grained, with strong cleavage",
            "hardness": "3–4 Mohs",
            "formation": (
                "Forms from low-grade metamorphism of shale or mudstone. "
                "Clay minerals align under directed pressure creating slaty cleavage."
            ),
            "minerals": ["Clay minerals", "Mica", "Chlorite", "Quartz"],
            "characteristics": (
                "Splits into thin, flat sheets along cleavage planes. "
                "Very fine-grained. Dull luster on cleavage surfaces."
            ),
            "economic_importance": (
                "Roofing tiles, flooring, blackboards, and decorative stone. "
                "Traditional material for billiard tables."
            ),
            "geological_setting": (
                "Found in zones of low-grade regional metamorphism, "
                "commonly associated with fold-and-thrust belts."
            ),
        },

        "Gneiss": {
            "type": "metamorphic",
            "subtype": "foliated (high-grade)",
            "color": "light and dark banded (gray and black)",
            "texture": "coarse-grained with gneissic banding (foliation)",
            "hardness": "6–7 Mohs",
            "formation": (
                "Forms from high-grade metamorphism of granite, shale, or other "
                "rocks. Mineral segregation produces characteristic banding."
            ),
            "minerals": ["Quartz", "Feldspar", "Mica", "Amphibole", "Garnet"],
            "characteristics": (
                "Distinct alternating light and dark bands of minerals. "
                "Coarse-grained. Does not split as easily as schist."
            ),
            "economic_importance": (
                "Building stone, crushed aggregate, and decorative stone. "
                "Important component of Precambrian shields."
            ),
            "geological_setting": (
                "Found in deeply eroded mountain ranges and Precambrian "
                "shield areas. Associated with granulite and amphibolite facies."
            ),
        },

        "Diorite": {
            "type": "igneous",
            "subtype": "intrusive / plutonic",
            "color": "gray, dark gray",
            "texture": "coarse-grained (phaneritic)",
            "hardness": "5–6 Mohs",
            "formation": (
                "Forms from slow cooling of intermediate magma in the crust. "
                "Intermediate in composition between granite and gabbro."
            ),
            "minerals": ["Feldspar", "Amphibole", "Pyroxene", "Mica", "Quartz"],
            "characteristics": (
                "Salt-and-pepper appearance due to white plagioclase and "
                "dark hornblende. Lacks quartz or has very little."
            ),
            "economic_importance": (
                "Used as a construction and road building material. "
                "Historically used for sculpture."
            ),
            "geological_setting": (
                "Found in continental arcs and at convergent plate margins, "
                "often associated with granite and gabbro plutons."
            ),
        },

        "Gabbro": {
            "type": "igneous",
            "subtype": "intrusive / plutonic (mafic)",
            "color": "dark green to black",
            "texture": "coarse-grained (phaneritic)",
            "hardness": "5.5–6 Mohs",
            "formation": (
                "Forms from slow cooling of mafic magma deep in the crust. "
                "It is the intrusive equivalent of basalt."
            ),
            "minerals": ["Pyroxene", "Feldspar", "Olivine", "Amphibole", "Magnetite"],
            "characteristics": (
                "Dark-colored, coarse-grained rock. Dense and heavy. "
                "Low quartz content. Often contains visible olivine."
            ),
            "economic_importance": (
                "Host rock for Ni-Cu-PGE deposits. Used as dimension stone "
                "('black granite'). Important for ophiolite studies."
            ),
            "geological_setting": (
                "Oceanic crust, layered mafic intrusions, and the lower "
                "portions of ophiolite complexes."
            ),
        },

        "Rhyolite": {
            "type": "igneous",
            "subtype": "extrusive / volcanic (felsic)",
            "color": "light pink, gray, or cream",
            "texture": "fine-grained or porphyritic with flow banding",
            "hardness": "6–7 Mohs",
            "formation": (
                "Forms from rapid cooling of felsic lava rich in silica. "
                "Erupted from continental volcanoes and calderas."
            ),
            "minerals": ["Quartz", "Feldspar", "Biotite", "Hornblende"],
            "characteristics": (
                "Light-colored fine-grained rock. May have flow banding "
                "or phenocrysts of quartz and feldspar. High silica content (>69%)."
            ),
            "economic_importance": (
                "Associated with epithermal gold-silver deposits. "
                "Used as building stone and in ceramics."
            ),
            "geological_setting": (
                "Continental volcanic arcs, calderas, and hot spot volcanoes "
                "overlying continental crust."
            ),
        },

        "Andesite": {
            "type": "igneous",
            "subtype": "extrusive / volcanic (intermediate)",
            "color": "gray, dark gray, or brown",
            "texture": "fine-grained, often porphyritic",
            "hardness": "5.5–6 Mohs",
            "formation": (
                "Forms from intermediate magmas at subduction zones. "
                "Erupted from stratovolcanoes at convergent margins."
            ),
            "minerals": ["Feldspar", "Pyroxene", "Amphibole", "Magnetite"],
            "characteristics": (
                "Gray, fine-grained volcanic rock. Phenocrysts of plagioclase "
                "common. Intermediate silica content (52–63%)."
            ),
            "economic_importance": (
                "Associated with porphyry copper-gold deposits. "
                "Used as aggregate. Important indicator of subduction tectonics."
            ),
            "geological_setting": (
                "Subduction zone volcanic arcs, island arcs, and "
                "continental volcanic belts."
            ),
        },

        "Obsidian": {
            "type": "igneous",
            "subtype": "extrusive / volcanic glass",
            "color": "black, brown, or gray",
            "texture": "glassy (no crystalline structure)",
            "hardness": "5–5.5 Mohs",
            "formation": (
                "Forms from extremely rapid cooling of felsic lava, "
                "preventing crystal growth. Natural volcanic glass."
            ),
            "minerals": ["Volcanic glass (amorphous silica)"],
            "characteristics": (
                "Shiny, glassy appearance. Conchoidal fracture with sharp edges. "
                "Translucent to opaque. Very smooth surface."
            ),
            "economic_importance": (
                "Used in surgical scalpels (sharper than steel). "
                "Historically used as cutting tools and ornamental stone."
            ),
            "geological_setting": (
                "Found at lava flow margins, especially near calderas "
                "and rhyolitic volcanism."
            ),
        },

        "Pumice": {
            "type": "igneous",
            "subtype": "extrusive / pyroclastic",
            "color": "white, light gray, or cream",
            "texture": "highly vesicular, porous (foam-like)",
            "hardness": "6 Mohs",
            "formation": (
                "Forms from gas-rich felsic magma that cools rapidly during "
                "explosive volcanic eruptions, trapping countless gas bubbles."
            ),
            "minerals": ["Volcanic glass", "Feldspar", "Quartz"],
            "characteristics": (
                "Extremely low density (floats on water). Highly porous "
                "and abrasive. Light-colored, frothy appearance."
            ),
            "economic_importance": (
                "Abrasive in personal care products, cosmetics, concrete "
                "production, horticulture, and water filtration."
            ),
            "geological_setting": (
                "Found near explosive rhyolitic and dacitic volcanoes, "
                "tephra deposits, and pyroclastic flow deposits."
            ),
        },
    },

    # -----------------------------------------------------------------------
    # MINERALS
    # -----------------------------------------------------------------------
    "minerals": {

        "Quartz": {
            "formula": "SiO₂",
            "hardness": "7 Mohs",
            "color": "colorless, white, pink, purple, smoky",
            "luster": "vitreous",
            "cleavage": "none (conchoidal fracture)",
            "description": (
                "Most abundant mineral in the Earth's crust. Very hard and resistant "
                "to weathering. Component of granite, sandstone, and many other rocks. "
                "Varieties include amethyst, rose quartz, and smoky quartz."
            ),
            "occurrence": "Igneous, sedimentary, and metamorphic rocks",
            "economic_uses": "Glass, electronics (piezoelectric), abrasives, gems",
        },

        "Feldspar": {
            "formula": "KAlSi₃O₈ / NaAlSi₃O₈ / CaAl₂Si₂O₈",
            "hardness": "6–6.5 Mohs",
            "color": "white, pink, gray, cream",
            "luster": "vitreous to pearly",
            "cleavage": "two directions at 90° or 86°",
            "description": (
                "Most abundant mineral group in the crust (~60% of crust). "
                "Includes orthoclase, plagioclase, and microcline. "
                "Essential component of granite, diorite, and andesite."
            ),
            "occurrence": "Igneous, metamorphic, and sedimentary rocks",
            "economic_uses": "Ceramics, glass, enamel, detergents",
        },

        "Mica": {
            "formula": "K(Mg,Fe)₃AlSi₃O₁₀(OH)₂",
            "hardness": "2–4 Mohs",
            "color": "silver, gold, black (biotite), colorless (muscovite)",
            "luster": "pearly, vitreous",
            "cleavage": "perfect basal cleavage (one direction)",
            "description": (
                "Group of sheet silicate minerals with perfect basal cleavage. "
                "Biotite is dark (iron-rich), muscovite is light (potassium-rich). "
                "Common in granite, schist, and gneiss."
            ),
            "occurrence": "Igneous, metamorphic rocks",
            "economic_uses": "Electrical insulation, cosmetics, paints, joint compound",
        },

        "Calcite": {
            "formula": "CaCO₃",
            "hardness": "3 Mohs",
            "color": "colorless, white, gray, yellow",
            "luster": "vitreous to resinous",
            "cleavage": "perfect rhombohedral in 3 directions",
            "description": (
                "Primary mineral in limestone and marble. Effervesces vigorously "
                "with dilute HCl. Exhibits double refraction. Very common mineral "
                "in carbonate rocks and caves (stalactites)."
            ),
            "occurrence": "Limestone, marble, hydrothermal veins, cave deposits",
            "economic_uses": "Cement, lime, steel production, paper, pharmaceuticals",
        },

        "Dolomite": {
            "formula": "CaMg(CO₃)₂",
            "hardness": "3.5–4 Mohs",
            "color": "white, gray, pink",
            "luster": "vitreous to pearly",
            "cleavage": "perfect rhombohedral in 3 directions",
            "description": (
                "Calcium-magnesium carbonate mineral. Similar to calcite but reacts "
                "weakly with cold HCl. Forms dolostone when rock-forming. "
                "Often replaces limestone through dolomitization."
            ),
            "occurrence": "Dolostone, marble, hydrothermal veins",
            "economic_uses": "Building stone, cement, magnesium source, ceramics",
        },

        "Pyrite": {
            "formula": "FeS₂",
            "hardness": "6–6.5 Mohs",
            "color": "pale brass-yellow (fool's gold)",
            "luster": "metallic",
            "cleavage": "poor (cubic fracture)",
            "description": (
                "Iron sulfide, known as 'fool's gold' due to its golden color. "
                "Common in many geological environments. Indicator of reducing "
                "conditions. Associated with ore deposits."
            ),
            "occurrence": "Sedimentary, igneous, hydrothermal ore deposits",
            "economic_uses": "Sulfuric acid production, source of sulfur, iron ore",
        },

        "Magnetite": {
            "formula": "Fe₃O₄",
            "hardness": "5.5–6.5 Mohs",
            "color": "black",
            "luster": "metallic to submetallic",
            "cleavage": "none",
            "description": (
                "Strongly magnetic iron oxide mineral. One of the main iron ores. "
                "Common accessory mineral in mafic igneous rocks. "
                "Natural magnets (lodestones) are magnetite."
            ),
            "occurrence": "Mafic igneous rocks, metamorphic rocks, ore deposits",
            "economic_uses": "Iron and steel production, magnetic applications",
        },

        "Olivine": {
            "formula": "(Mg,Fe)₂SiO₄",
            "hardness": "6.5–7 Mohs",
            "color": "olive-green to yellow-green",
            "luster": "vitreous",
            "cleavage": "imperfect in 2 directions",
            "description": (
                "Magnesium-iron silicate, major component of Earth's mantle. "
                "Common in mafic and ultramafic rocks (basalt, gabbro, peridotite). "
                "Gem variety is peridot. Weathers to serpentine."
            ),
            "occurrence": "Mafic igneous rocks, ultramafic rocks, metamorphic rocks",
            "economic_uses": "Refractory material, sandblasting, gem (peridot)",
        },

        "Pyroxene": {
            "formula": "General: XYSi₂O₆ (X=Ca,Na; Y=Mg,Fe,Al)",
            "hardness": "5–7 Mohs",
            "color": "dark green, black, or brown",
            "luster": "vitreous",
            "cleavage": "two directions at ~87°",
            "description": (
                "Group of single-chain silicate minerals. Important rock-forming "
                "minerals in mafic and ultramafic rocks. Includes augite, enstatite, "
                "and diopside. Distinguishable from amphibole by cleavage angle."
            ),
            "occurrence": "Mafic igneous rocks, high-grade metamorphic rocks",
            "economic_uses": "Gemstones (jadeite), industrial applications",
        },

        "Amphibole": {
            "formula": "General: double-chain silicate (Ca,Na)₂(Mg,Fe,Al)₅Si₈O₂₂(OH)₂",
            "hardness": "5–6 Mohs",
            "color": "dark green, black, brown",
            "luster": "vitreous",
            "cleavage": "two directions at ~60° and 120°",
            "description": (
                "Group of double-chain silicate minerals. Hornblende is the most "
                "common variety. Important in intermediate and mafic rocks. "
                "Distinguished from pyroxene by cleavage angle (60°/120° vs 87°/93°)."
            ),
            "occurrence": "Intermediate igneous rocks, amphibolite facies metamorphics",
            "economic_uses": "Asbestos (tremolite-actinolite group) – now restricted",
        },

        "Chlorite": {
            "formula": "(Mg,Fe,Al)₆(Al,Si)₄O₁₀(OH)₈",
            "hardness": "2–3 Mohs",
            "color": "green",
            "luster": "vitreous to pearly",
            "cleavage": "perfect basal cleavage",
            "description": (
                "Phyllosilicate mineral common in low-grade metamorphic and "
                "hydrothermally altered rocks. Indicator of greenschist facies "
                "metamorphism. Often replaces biotite and hornblende."
            ),
            "occurrence": "Low-grade metamorphic rocks, hydrothermal alteration zones",
            "economic_uses": "Geological indicator mineral, some industrial uses",
        },

        "Serpentine": {
            "formula": "Mg₃Si₂O₅(OH)₄",
            "hardness": "3–5 Mohs",
            "color": "green, yellow-green, or mottled",
            "luster": "waxy to greasy",
            "cleavage": "imperfect",
            "description": (
                "Group of phyllosilicate minerals formed by hydrothermal alteration "
                "of olivine and pyroxene (serpentinization). Found in ophiolites "
                "and ultramafic rocks. Chrysotile (white asbestos) is a variety."
            ),
            "occurrence": "Ultramafic rocks, ophiolites, metamorphic terrains",
            "economic_uses": "Chrysotile asbestos (restricted), decorative stone",
        },
    },

    # -----------------------------------------------------------------------
    # GEOLOGICAL FORMATIONS
    # -----------------------------------------------------------------------
    "formations": {

        "Ophiolite": {
            "description": (
                "A section of oceanic crust and upper mantle that has been emplaced "
                "onto continental crust through obduction. Consists of (from bottom): "
                "peridotite, gabbro, sheeted dikes, pillow basalts, and marine sediments."
            ),
            "economic_significance": "Host for Ni-Cu-PGE and chromite deposits",
        },

        "Batholith": {
            "description": (
                "A large mass of intrusive igneous rock (>100 km²) exposed at the surface "
                "by erosion. Composed mainly of granite and granodiorite. "
                "Forms the core of many mountain ranges."
            ),
            "economic_significance": "Host for porphyry Cu-Mo, Au-Ag deposits",
        },

        "Sedimentary Basin": {
            "description": (
                "A region of prolonged subsidence where sediments accumulate to great "
                "thickness. Contains important petroleum systems and groundwater aquifers. "
                "Bounded by faults or flexural loading."
            ),
            "economic_significance": "Oil, gas, coal, groundwater, and mineral resources",
        },

        "Metamorphic Belt": {
            "description": (
                "Linear zone of metamorphic rocks formed during orogenic events. "
                "Shows progressive metamorphic grades from low (chlorite zone) to "
                "high (sillimanite zone) inward."
            ),
            "economic_significance": "Gold, base metals, gem deposits",
        },

        "Greenstone Belt": {
            "description": (
                "Archean sequences of volcanic and sedimentary rocks that have "
                "undergone low-grade metamorphism. Major host of orogenic gold deposits "
                "and Archean mineral wealth."
            ),
            "economic_significance": "Gold, Ni-Cu, VMS (Zn-Cu-Pb) deposits",
        },

        "Carbonate Platform": {
            "description": (
                "Broad, shallow marine environment where carbonate sediments accumulate. "
                "Forms limestone, dolostone, and reef complexes. "
                "Important petroleum reservoirs and aquifers."
            ),
            "economic_significance": "Oil and gas reservoirs, groundwater, building stone",
        },
    },

    # -----------------------------------------------------------------------
    # GENERAL GEOLOGICAL CONTEXT
    # -----------------------------------------------------------------------
    "general": {
        "drill_core_description": (
            "Drill core samples are cylindrical rock specimens extracted during rotary "
            "or diamond drilling. They provide continuous subsurface information about "
            "lithology, structure, mineralogy, and alteration. Core logging is the "
            "systematic description of these samples."
        ),
        "lithology_classification": (
            "Lithology classification involves identifying rock types based on mineral "
            "composition, texture, color, grain size, and structural features. Machine "
            "learning models trained on drill core images can automate this process, "
            "reducing costs and improving consistency."
        ),
        "confidence_interpretation": {
            "very_high": "≥ 90% — High confidence; classification is reliable",
            "high": "70–89% — Good confidence; minor ambiguity possible",
            "moderate": "50–69% — Moderate confidence; consider visual verification",
            "low": "< 50% — Low confidence; manual review strongly recommended",
        },
    },
}
