import re
from typing import Optional

# ---------------------------------------------------------------------------
# Hanoi aliases (Vietnamese, English, common typos)
# ---------------------------------------------------------------------------
_HANOI_PATTERNS = [
    r"\bh[àa]\s*n[ộo]i\b",
    r"\bhanoi\b",
    r"\bhn\b",
    r"\bth[uủ]\s*đ[ôo]\b",          # "thủ đô"
    r"\bth[uủ]\s*do\b",
]

# ---------------------------------------------------------------------------
# Other Vietnamese provinces / cities that are NOT Hanoi
# (non-exhaustive but covers the most common ones)
# ---------------------------------------------------------------------------
_OTHER_CITY_PATTERNS = [
    r"\bh[oò]\s*ch[ií]\s*minh\b",
    r"\bsaigon\b", r"\bs[àa]i\s*g[òo]n\b",
    r"\bhcm\b",
    r"\bđ[àa]\s*n[ẵa]ng\b", r"\bda\s*nang\b",
    r"\bh[ảa]i\s*ph[òo]ng\b", r"\bhai\s*phong\b",
    r"\bhu[ếe]\b",
    r"\bh[ộo]i\s*an\b", r"\bhoi\s*an\b",
    r"\bn[hh]a\s*trang\b",
    r"\bđ[àa]\s*l[ạa]t\b", r"\bda\s*lat\b",
    r"\bv[ũu]ng\s*t[àa]u\b",
    r"\bph[úu]\s*qu[ốo]c\b", r"\bphu\s*quoc\b",
    r"\bqu[ảa]ng\s*ninh\b",
    r"\bh[ạa]\s*long\b", r"\bha\s*long\b",
    r"\bni[nh]\s*b[ìi]nh\b",
    r"\bs[ơo]n\s*la\b",
    r"\bl[àa]o\s*cai\b",
    r"\bs[ạa]pa\b",
    r"\bm[ộo]c\s*ch[âa]u\b",
    r"\bth[áa]i\s*nguy[êe]n\b",
    r"\bnam\s*đ[ịi]nh\b",
    r"\bh[àa]\s*t[ĩi]nh\b",
    r"\bvinh\b",
    r"\bqu[ảa]ng\s*b[ìi]nh\b",
    r"\bqu[ảa]ng\s*tr[ịi]\b",
    r"\bqu[ảa]ng\s*ng[ãa]i\b",
    r"\bqu[ảa]ng\s*nam\b",
    r"\bb[ìi]nh\s*đ[ịi]nh\b",
    r"\bph[úu]\s*y[êe]n\b",
    r"\bkh[áa]nh\s*h[òo]a\b",
    r"\bninh\s*thu[ậa]n\b",
    r"\bb[ìi]nh\s*thu[ậa]n\b",
    r"\blong\s*an\b",
    r"\bti[êe]n\s*giang\b",
    r"\bc[àa]n\s*th[ơo]\b",
    r"\bki[êe]n\s*giang\b",
    r"\ban\s*giang\b",
    r"\bđ[ồo]ng\s*th[áa]p\b",
    r"\bv[ĩi]nh\s*long\b",
    r"\bb[ếe]n\s*tre\b",
    r"\btr[àa]\s*vinh\b",
    r"\bs[óo]c\s*tr[ăa]ng\b",
    r"\bb[ạa]c\s*li[êe]u\b",
    r"\bc[àa]\s*mau\b",
    r"\bđ[ắa]k\s*l[ắa]k\b",
    r"\bđ[ắa]k\s*n[ôo]ng\b",
    r"\bgia\s*lai\b",
    r"\bkon\s*tum\b",
    r"\bl[âa]m\s*đ[ồo]ng\b",
    r"\bb[ìi]nh\s*ph[ướu][ớo]c\b",
    r"\bt[âa]y\s*ninh\b",
    r"\bb[ìi]nh\s*d[ươu][ơo]ng\b",
    r"\bđ[ồo]ng\s*nai\b",
    r"\bb[àa]\s*r[ịi]a\b",
    r"\bth[áa]i\s*b[ìi]nh\b",
    r"\bh[àa]\s*nam\b",
    r"\bh[ưu][ơo]ng\s*y[êe]n\b",
    r"\bh[ảa]i\s*d[ươu][ơo]ng\b",
    r"\bb[ắa]c\s*ninh\b",
    r"\bv[ĩi]nh\s*ph[úu]c\b",
    r"\bh[òo]a\s*b[ìi]nh\b",
    r"\bph[úu]\s*th[ọo]\b",
    r"\by[êe]n\s*b[áa]i\b",
    r"\bl[ạa]ng\s*s[ơo]n\b",
    r"\bb[ắa]c\s*giang\b",
    r"\bb[ắa]c\s*k[ạa]n\b",
    r"\bcao\s*b[ằa]ng\b",
    r"\bh[àa]\s*giang\b",
    r"\btuyen\s*quang\b",
    r"\bth[áa]nh\s*h[óo]a\b",
    r"\bđi[êe]n\s*bi[êe]n\b",
    r"\blai\s*ch[âa]u\b",
]

# ---------------------------------------------------------------------------
# Foreign countries and international cities (NOT Vietnam)
# ---------------------------------------------------------------------------
_FOREIGN_LOCATION_PATTERNS = [
    # Southeast Asia
    r"\bthailand\b", r"\bth[áa]i\s*lan\b",
    r"\bbangkok\b",
    r"\bsingapore\b", r"\bsing[aá]\s*po\b",
    r"\bmalaysia\b", r"\bma\s*lai\s*xi[aá]\b",
    r"\bkuala\s*lumpur\b",
    r"\bindonesia\b", r"\bin\s*đ[ôo]\s*n[êe]\s*xi[aá]\b",
    r"\bjakarta\b", r"\bbali\b",
    r"\bphilippines\b", r"\bmanila\b",
    r"\bmyanmar\b", r"\bburma\b",
    r"\bcambodia\b", r"\bcampuchia\b", r"\bphnom\s*penh\b",
    r"\blaos\b", r"\bl[àa]o\b", r"\bvientiane\b",
    
    # East Asia
    r"\bjapan\b", r"\bnhật\s*bản\b", r"\bnhat\s*ban\b",
    r"\btokyo\b", r"\bosaka\b", r"\bkyoto\b",
    r"\bkorea\b", r"\bh[àa]n\s*qu[ốo]c\b", r"\bhan\s*quoc\b",
    r"\bseoul\b", r"\bbusan\b",
    r"\bchina\b", r"\btrung\s*qu[ốo]c\b", r"\btrung\s*quoc\b",
    r"\bbeijing\b", r"\bshanghai\b", r"\bhong\s*kong\b",
    r"\btaiwan\b", r"\btai\s*wan\b", r"\btaipei\b",
    
    # Europe
    r"\bfrance\b", r"\bph[áa]p\b",
    r"\bparis\b", r"\bpa\s*ri\b",
    r"\buk\b", r"\bengland\b", r"\banh\b",
    r"\blondon\b",
    r"\bgermany\b", r"\bđ[ứu]c\b",
    r"\bberlin\b", r"\bmunich\b",
    r"\bitaly\b", r"\b[ýy]\b",
    r"\brome\b", r"\bmilan\b", r"\bvenice\b",
    r"\bspain\b", r"\btay\s*ban\s*nha\b",
    r"\bmadrid\b", r"\bbarcelona\b",
    r"\brussels\b", r"\bamsterdam\b", r"\bvienna\b",
    
    # Americas
    r"\busa\b", r"\bamerica\b", r"\bm[ỹy]\b",
    r"\bnew\s*york\b", r"\blos\s*angeles\b", r"\bsan\s*francisco\b",
    r"\bcanada\b", r"\btoronto\b", r"\bvancouver\b",
    r"\bbrazil\b", r"\brio\b", r"\bsao\s*paulo\b",
    
    # Middle East & Others
    r"\bdubai\b", r"\babu\s*dhabi\b",
    r"\bturkey\b", r"\bistanbul\b",
    r"\baustralia\b", r"\b[úu]c\b", r"\bsydney\b", r"\bmelbourne\b",
    r"\bindia\b", r"\b[ấấ]n\s*đ[ộo]\b", r"\bdelhi\b", r"\bmumbai\b",
]

# ---------------------------------------------------------------------------
# Non-travel/food topics that should be rejected
# ---------------------------------------------------------------------------
_IRRELEVANT_TOPIC_PATTERNS = [
    # Technology & Programming
    r"\bpython\b", r"\bjavascript\b", r"\breact\b", r"\bnode\.?js\b",
    r"\bcode\b", r"\bcoding\b", r"\bprogram\b", r"\bsoftware\b",
    r"\bapi\b", r"\bdatabase\b", r"\bserver\b",
    r"\bai\b", r"\bmachine\s*learning\b", r"\bdeep\s*learning\b",
    
    # Health & Medicine
    r"\bthuốc\b", r"\bbệnh\b", r"\bkh[áa]m\s*bệnh\b",
    r"\bmedicine\b", r"\bdoctor\b", r"\bhospital\b",
    r"\bvaccine\b", r"\btreatment\b",
    
    # Finance & Business
    r"\bstock\b", r"\bc[ổô]\s*phi[ếế]u\b",
    r"\binvest\b", r"\bđ[ầầ]u\s*t[ưư]\b",
    r"\bbank\b", r"\bng[âa]n\s*h[àa]ng\b",
    r"\bloan\b", r"\bcredit\b", r"\binsurance\b",
    
    # Education (non-travel related)
    r"\bhọc\s*t[ậậ]p\b", r"\bstudy\b",
    r"\bexam\b", r"\btest\b", r"\bhomework\b",
    r"\buniversity\b", r"\bcollege\b",
    
    # Politics & Social Issues
    r"\bch[ííí]nh\s*tr[ịị]\b", r"\bpolitics\b",
    r"\belection\b", r"\bgovernment\b",
    r"\bwar\b", r"\bconflict\b",
    
    # Sports (non-travel related)
    r"\bfootball\b", r"\bsoccer\b", r"\bbasketball\b",
    r"\bworld\s*cup\b", r"\bolympic\b",
    
    # Entertainment (non-travel related)
    r"\bmovie\b", r"\bfilm\b", r"\bcinema\b",
    r"\bmusic\b", r"\bconcert\b", r"\bsong\b",
    
    # Prompt Injection Attempts
    r"\bignore\s+(previous|above|prior)\s+instructions?\b",
    r"\bsystem\s+prompt\b",
    r"\byou\s+are\s+now\b",
    r"\bpretend\s+to\s+be\b",
    r"\bact\s+as\b",
    r"\bwrite\s+(me\s+)?a\s+(poem|story|essay)\b",
    r"\bsolve\s+(this|the)\s+(math|problem)\b",
    r"\btranslate\b.*\bto\b",
]

# ---------------------------------------------------------------------------
# Keywords that indicate a travel/food/tour-related request
# ---------------------------------------------------------------------------
_TRAVEL_KEYWORDS = [
    r"\btour\b", r"\blich\s*trinh\b", r"\blịch\s*trình\b",
    r"\bdu\s*l[ịi]ch\b", r"\bdi\s*ch[ơo]i\b", r"\bđi\s*ch[ơo]i\b",
    r"\ban\s*u[ốo]ng\b", r"\bnh[àa]\s*h[àa]ng\b", r"\bqu[áa]n\b",
    r"\bth[ăa]m\s*quan\b", r"\btham\s*quan\b",
    r"\bđ[ịi]a\s*đi[ểe]m\b", r"\bdia\s*diem\b",
    r"\bh[àa]\s*n[ộo]i\b", r"\bhanoi\b",
    r"\bsightseeing\b", r"\bdining\b", r"\bfood\b", r"\beat\b",
    r"\btravel\b", r"\btrip\b", r"\bitinerary\b",
    r"\bng[àa]y\b",   # "1 ngay", "2 ngay"
    r"\bbu[ổo]i\b",   # "buoi sang", "buoi toi"
    r"\bs[áa]ng\b", r"\btr[ưu]a\b", r"\bt[ốo]i\b",  # meal times
    r"\bmonument\b", r"\btemple\b", r"\bpagoda\b", r"\bpark\b",
    r"\bch[ùu]a\b", r"\bđ[ềe]n\b", r"\bh[ồo]\b",  # chua, den, ho
]


def _match_any(text: str, patterns: list[str]) -> bool:
    lower = text.lower()
    return any(re.search(p, lower) for p in patterns)


class TourInputError(ValueError):
    """Raised when the user's prompt fails validation."""
    pass


def validate_tour_prompt(prompt: str) -> None:
    """
    Validate the tour generation prompt.

    Raises TourInputError with a user-friendly Vietnamese message if:
    - The prompt is too short / looks like gibberish
    - The prompt mentions a city/province other than Hanoi
    - The prompt mentions foreign countries/cities
    - The prompt contains irrelevant topics (tech, health, finance, etc.)
    - The prompt has no travel/food-related keywords
    """
    stripped = prompt.strip()

    # 1. Basic length check
    if len(stripped) < 5:
        raise TourInputError(
            "Yêu cầu quá ngắn. Vui lòng mô tả rõ hơn bạn muốn tạo tour như thế nào."
        )

    # 2. Gibberish / random characters check
    #    If the ratio of non-alphanumeric (excluding spaces) is too high → likely spam
    alpha_count = sum(1 for c in stripped if c.isalpha())
    if len(stripped) > 0 and alpha_count / len(stripped) < 0.3:
        raise TourInputError(
            "Yêu cầu không hợp lệ. Vui lòng nhập mô tả tour bằng tiếng Việt hoặc tiếng Anh."
        )

    # 3. Block other Vietnamese cities/provinces
    if _match_any(stripped, _OTHER_CITY_PATTERNS):
        raise TourInputError(
            "Hiện tại hệ thống chỉ hỗ trợ tạo tour tại Hà Nội. "
            "Vui lòng thử lại với yêu cầu tour Hà Nội."
        )

    # 4. Block foreign countries and international cities
    if _match_any(stripped, _FOREIGN_LOCATION_PATTERNS):
        raise TourInputError(
            "Hiện tại hệ thống chỉ hỗ trợ tạo tour tại Hà Nội, Việt Nam. "
            "Chúng tôi không hỗ trợ tour quốc tế. "
            "Vui lòng thử lại với yêu cầu tour Hà Nội."
        )

    # 5. Block irrelevant topics (tech, health, finance, prompt injection, etc.)
    if _match_any(stripped, _IRRELEVANT_TOPIC_PATTERNS):
        raise TourInputError(
            "Yêu cầu không liên quan đến du lịch hoặc ẩm thực tại Hà Nội. "
            "Hệ thống chỉ hỗ trợ tạo lịch trình tour, ăn uống và tham quan. "
            "Vui lòng nhập yêu cầu hợp lệ, ví dụ: \"Tour 1 ngày Hà Nội ăn uống và tham quan\"."
        )

    # 6. Must contain at least one travel/food keyword
    if not _match_any(stripped, _TRAVEL_KEYWORDS):
        raise TourInputError(
            "Yêu cầu không liên quan đến du lịch hoặc ẩm thực. "
            "Vui lòng nhập yêu cầu tạo lịch trình tour, ví dụ: "
            "\"Tour 1 ngày Hà Nội ăn uống và tham quan\"."
        )


def validate_modify_feedback(prompt: str) -> None:

    stripped = prompt.strip()

    # 1. Basic length check
    if len(stripped) < 3:
        raise TourInputError(
            "Yêu cầu quá ngắn. Vui lòng mô tả rõ hơn bạn muốn chỉnh sửa gì."
        )

    # 2. Gibberish check
    alpha_count = sum(1 for c in stripped if c.isalpha())
    if len(stripped) > 0 and alpha_count / len(stripped) < 0.3:
        raise TourInputError(
            "Yêu cầu không hợp lệ. Vui lòng nhập mô tả bằng tiếng Việt hoặc tiếng Anh."
        )

    # 3. Block other Vietnamese cities/provinces
    if _match_any(stripped, _OTHER_CITY_PATTERNS):
        raise TourInputError(
            "Hiện tại hệ thống chỉ hỗ trợ tour tại Hà Nội. "
            "Vui lòng thử lại với yêu cầu tour Hà Nội."
        )

    # 4. Block foreign countries and international cities
    if _match_any(stripped, _FOREIGN_LOCATION_PATTERNS):
        raise TourInputError(
            "Hiện tại hệ thống chỉ hỗ trợ tour tại Hà Nội, Việt Nam. "
            "Chúng tôi không hỗ trợ tour quốc tế."
        )

    # 5. Block irrelevant topics
    if _match_any(stripped, _IRRELEVANT_TOPIC_PATTERNS):
        raise TourInputError(
            "Yêu cầu không liên quan đến du lịch hoặc ẩm thực tại Hà Nội. "
            "Vui lòng chỉ yêu cầu chỉnh sửa liên quan đến lịch trình tour."
        )
