"""
Test fixtures for the PySmash scraper tests.
"""

# Sample HTML content for testing scrapers
SAMPLE_SET_PAGE_HTML = """
<html>
<body>
    <div id="gallery-0">
        <img src="robot.jpg" alt="Robots" />
        <img src="dinosaur.jpg" alt="Dinosaurs" />
        <img src="wizard.jpg" alt="Wizards" />
    </div>
</body>
</html>
"""

SAMPLE_FACTION_PAGE_HTML = """
<html>
<body>
    <p>
        <span id="Robot_Walker">Robot Walker</span> - power 3 - Move a minion to another base.
    </p>
    <p>
        <span id="Laser_Blast">Laser Blast</span> - Destroy a minion with power 3 or less.
    </p>
    <p>
        <span id="Metal_Detector">Metal Detector</span> - power 2 - Search the discard pile for an action and play it.
    </p>
</body>
</html>
"""

SAMPLE_BASES_PAGE_HTML = """
<html>
<body>
    <ul>
        <li>The School - breakpoint 15 - VPs: 4 2 1 - Students get +1 power.</li>
        <li>The Mall - breakpoint 20 - VPs: 6 3 1 - After each player's turn, they may draw a card.</li>
        <li>Cave of Shinies - breakpoint 12 - VPs: 3 2 1 - Minions here cannot use their abilities.</li>
    </ul>
</body>
</html>
"""

# Sample data models for testing
SAMPLE_SET_DATA = {
    "set_id": "sample_set_id_123",
    "set_name": "Core_Set",
    "set_url": "https://smashup.fandom.com/wiki/Core_Set"
}

SAMPLE_FACTION_DATA = {
    "faction_id": "sample_faction_id_123",
    "faction_name": "Robots",
    "faction_url": "https://smashup.fandom.com/wiki/Robots",
    "set_id": "sample_set_id_123"
}

SAMPLE_MINION_CARD = {
    "name": "Robot Walker",
    "description": "Move a minion to another base.",
    "faction_name": "Robots",
    "faction_id": "sample_faction_id_123",
    "power": 3
}

SAMPLE_ACTION_CARD = {
    "name": "Laser Blast",
    "description": "Destroy a minion with power 3 or less.",
    "faction_name": "Robots",
    "faction_id": "sample_faction_id_123"
}

SAMPLE_BASE_CARD = {
    "base_name": "The School",
    "base_power": 15,
    "base_desc": "Students get +1 power.",
    "first_place": 4,
    "second_place": 2,
    "third_place": 1
}

# Mock response data for web client testing
MOCK_WEB_RESPONSES = {
    "Core_Set": SAMPLE_SET_PAGE_HTML,
    "Robots": SAMPLE_FACTION_PAGE_HTML,
    "Bases": SAMPLE_BASES_PAGE_HTML
}

# Error scenarios for testing
ERROR_SCENARIOS = {
    "network_timeout": "Request timed out",
    "invalid_html": "<html><invalid></html>",
    "empty_response": "",
    "server_error": "Internal Server Error"
}
