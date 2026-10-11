from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def clean_speaker_name(raw_id: str | None) -> str:
    if not raw_id:
        return "Narrator"

    name = raw_id.strip()
    # Strip common suffixes
    name = re.sub(r"(_NULL)+$", "", name)
    name = re.sub(r"^NKM_UNIT_", "", name)
    name = re.sub(r"^NKM_NPC_", "", name)

    # Specific friendly mappings
    replacements = {
        "YOO_MINA": "Yoo Mina",
        "HILDE": "Hilde",
        "JOO_SHIYOON": "Joo Shiyoon",
        "SEO_YOON": "Seo Yoon",
        "XIAO_LIN": "Xiao Lin",
        "KIM_SOBIN": "Kim Sobin",
        "YOO_JIN": "Yoo Jin",
        "CIEL_ACADEMY": "Ciel",
        "CIEL": "Ciel",
        "LONE_LEE": "Lone Lee",
        "SHIREN": "Shiren",
        "GAEUN": "Gaeun",
        "LEE_YUMI": "Lee Yumi",
        "SIGMA": "Sigma",
        "HORIZON": "Horizon",
        "RITA_ARSENICO": "Rita Arsenico",
        "MINISTRY_CHLOE": "Chloe",
        "MEMBER_CLAN_WHITE": "White Clan Member",
        "POOR_NPC": "Citizen",
    }
    for k, v in replacements.items():
        if k in name:
            return v

    # Fallback: prettify words
    parts = [w.capitalize() for w in name.split("_") if w]
    return " ".join(parts) if parts else "Narrator"


def categorize_cutscene_id(cutscene_id: str) -> tuple[str, str, str]:
    cid = cutscene_id.upper()

    # Main Stream
    ep_match = re.match(r"EP(\d+)", cid)
    if ep_match:
        ep_num = int(ep_match.group(1))
        return "Main Stream", f"Episode {ep_num}", cutscene_id

    # CounterCase
    if cid.startswith("COUNTERCASE"):
        parts = cid.split("_")
        char_tag = parts[1] if len(parts) > 1 else "General"
        return "CounterCase", char_tag.capitalize(), cutscene_id

    # Side stories and events
    event_names = {
        "ACADEMY": "Old Administration Academy",
        "ADMIN": "Administration Failure",
        "ALPHA": "Alpharix",
        "AVENGER": "For the Uncrying",
        "BARCODE": "Bar Code",
        "BORDER": "Border Society",
        "CARNIVAL": "Carnival",
        "CHARADE": "Charade",
        "CLB": "Collab Event",
        "COLLABO": "Collab Event",
        "DJEHUTY": "Djehuty",
        "DOLL": "Lone puppet",
        "ESPR": "ESPR Squad",
        "HORIZON": "Horizon Finance",
        "MAID": "Mansion of Shadows",
        "MILITIA": "Militia",
        "NANAHARA": "Nanahara Family Alliance",
        "ORCA": "Orca",
        "PRIDE": "Great Witch's Legacy",
        "SIGMA": "Alone in the World (Sigma)",
        "STREGA": "Strega Witch Café",
        "VARUNA": "Sacred Spring of Varuna",
        "YAKSHA": "Yaksha",
    }
    for prefix, arc_title in event_names.items():
        if cid.startswith(prefix):
            return "Side Stories & Events", arc_title, cutscene_id

    return "Special & Misc", "General", cutscene_id


def parse_cutscene_file(
    json_path: Path,
    backgrounds_dir: Path | None = None,
) -> dict[str, Any] | None:
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception:
        return None

    records = data.get("records", [])
    if not records:
        return None

    cid = json_path.stem
    category, arc_title, clean_title = categorize_cutscene_id(cid)

    beats: list[dict[str, Any]] = []
    current_bg: str | None = None

    for idx, r in enumerate(records, start=1):
        # Update current background if set
        bg_name = r.get("m_BGFileName")
        if bg_name and isinstance(bg_name, str):
            bg_clean = bg_name.lower().strip()
            if bg_clean not in ("black", "white", "none", ""):
                current_bg = f"{bg_clean}.png"
                if backgrounds_dir and not (backgrounds_dir / current_bg).exists():
                    # Check without .png or variants
                    matches = list(backgrounds_dir.glob(f"{bg_clean}*.png"))
                    if matches:
                        current_bg = matches[0].name

        talk_eng = r.get("m_Talk_ENG")
        talk_vtn = r.get("m_Talk_VTN")
        talk_jpn = r.get("m_Talk_JPN")

        # Skip technical records with no speech or significant action
        if not talk_eng and not talk_vtn and not r.get("m_bWaitClick"):
            continue

        raw_char = r.get("m_CharStrID")
        speaker = clean_speaker_name(raw_char)

        clean_text = ""
        if isinstance(talk_eng, str) and len(talk_eng.strip()) > 0 and not talk_eng.startswith("(ENG)"):
            clean_text = talk_eng.strip()
        elif isinstance(talk_vtn, str) and len(talk_vtn.strip()) > 0:
            clean_text = talk_vtn.strip()
        elif isinstance(talk_eng, str):
            clean_text = talk_eng.replace("(ENG)", "").strip()

        if not clean_text and not r.get("m_StartFXSoundName"):
            continue

        pos = r.get("m_Pos", "C")
        pos_clean = "center"
        if "L" in str(pos):
            pos_clean = "left"
        elif "R" in str(pos):
            pos_clean = "right"

        beats.append({
            "step": idx,
            "speaker": speaker,
            "speaker_raw": raw_char or "",
            "dialogue": clean_text,
            "background": current_bg,
            "position": pos_clean,
            "face": r.get("m_Face", 0),
            "bgm": r.get("m_StartBGMFileName"),
            "sound": r.get("m_StartFXSoundName"),
        })

    if not beats:
        return None

    return {
        "id": cid,
        "title": clean_title.replace("_", " ").title(),
        "category": category,
        "arc": arc_title,
        "total_beats": len(beats),
        "beats": beats,
    }
