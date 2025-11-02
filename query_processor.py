import os
import re
import sqlite3
from typing import Dict, List, Any, Tuple

class QueryProcessor:
    """Simple pattern-based NLP processor for groundwater queries"""
    
    def __init__(self, db_path=None):
        if db_path is None:
            # Resolve path: backend/.. → project root → data/ingres_mock.db
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, "data", "ingres_mock.db")
        self.db_path = db_path
        self.intent_patterns = self._initialize_patterns()

    
    def _initialize_patterns(self) -> Dict[str, List[Tuple[str, str]]]:
        """Initialize intent patterns for query classification"""
        return {
            'groundwater_status': [
                (r'(what|show|tell).*(groundwater|water).*status.*(of|in|for)\s+(\w+)', 'location_query'),
                (r'status.*(of|in|for)\s+(\w+)', 'location_query'),
                (r'groundwater.*(\w+)\s+(district|block|state)', 'location_query'),
            ],
            'critical_areas': [
                (r'(show|list|which).*(critical|over-exploited|danger)', 'critical_query'),
                (r'areas.*(critical|over-exploited|danger)', 'critical_query'),
                (r'(critical|over-exploited).*(areas|blocks|districts)', 'critical_query'),
            ],
            'safe_areas': [
                (r'(show|list|which).*(safe|good).*areas', 'safe_query'),
                (r'areas.*safe', 'safe_query'),
                (r'safe.*(areas|blocks|districts)', 'safe_query'),
            ],
            'water_level': [
                (r'water level.*(of|in|for)\s+(\w+)', 'water_level_query'),
                (r'(depth|level).*water.*(of|in|for)\s+(\w+)', 'water_level_query'),
                (r'how deep.*water.*(in|at)\s+(\w+)', 'water_level_query'),
            ],
            'historical': [
                (r'(historical|history|trend|past).*(data|information|records)', 'historical_query'),
                (r'(show|get).*(trend|historical)', 'historical_query'),
                (r'data.*(from|between)\s+(\d{4})', 'historical_query'),
            ],
            'recharge': [
                (r'(recharge|replenishment).*(rate|data|information)', 'recharge_query'),
                (r'annual.*recharge', 'recharge_query'),
                (r'groundwater.*recharge', 'recharge_query'),
            ],
            'extraction': [
                (r'(extraction|withdrawal|usage).*(rate|data|information)', 'extraction_query'),
                (r'how much.*extract', 'extraction_query'),
                (r'groundwater.*(extraction|usage)', 'extraction_query'),
            ],
            'comparison': [
                (r'compare.*(between|with)', 'comparison_query'),
                (r'difference.*between', 'comparison_query'),
                (r'(better|worse).*than', 'comparison_query'),
            ],
            'help': [
                (r'(help|what can you do|features|capabilities)', 'help_query'),
                (r'how.*(to use|does.*work)', 'help_query'),
            ]
        }
    
    def classify_intent(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """Classify user query intent and extract entities"""
        query_lower = query.lower()
        
        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern, _ in patterns:
                match = re.search(pattern, query_lower)
                if match:
                    entities = self._extract_entities(query_lower, intent, match)
                    return intent, entities
        
        # Default to general query if no pattern matches
        return 'general', self._extract_entities(query_lower, 'general', None)
    
    def _extract_entities(self, query: str, intent: str, match) -> Dict[str, Any]:
        """Extract entities like location names, years, etc."""
        entities = {}
        
        # Extract location names (states, districts, blocks)
        locations = self._extract_locations(query)
        if locations:
            entities['locations'] = locations
        
        # Extract years
        years = re.findall(r'\b(20\d{2})\b', query)
        if years:
            entities['years'] = [int(year) for year in years]
        
        # Extract categories
        categories = []
        if 'safe' in query:
            categories.append('Safe')
        if 'critical' in query:
            categories.append('Critical')
        if 'semi' in query or 'semi-critical' in query:
            categories.append('Semi-Critical')
        if 'over' in query or 'exploited' in query:
            categories.append('Over-Exploited')
        
        if categories:
            entities['categories'] = categories
        
        return entities
    
    def _extract_locations(self, query: str) -> List[str]:
        """Extract location names from query"""
        locations = []
        try:
            conn = sqlite3.connect(self.db_path, timeout=3)
            cursor = conn.cursor()
            
            # Check for state names
            cursor.execute("SELECT state_name FROM states")
            states = [row[0].lower() for row in cursor.fetchall()]
            
            # Check for district names
            cursor.execute("SELECT district_name FROM districts")
            districts = [row[0].lower() for row in cursor.fetchall()]
            
            # Check for block names
            cursor.execute("SELECT block_name FROM blocks")
            blocks = [row[0].lower() for row in cursor.fetchall()]
            
            query_words = query.lower().split()
            
            # Check for exact matches
            for word in query_words:
                if word in states:
                    locations.append(word.title())
                elif word in [d.split()[0].lower() for d in districts]:
                    for d in districts:
                        if d.startswith(word):
                            locations.append(d.title())
                            break
            
            # Check for multi-word matches
            query_lower = query.lower()
            for state in states:
                if state in query_lower:
                    locations.append(state.title())
            
            for district in districts:
                if district in query_lower:
                    locations.append(district.title())
            
            for block in blocks:
                if block in query_lower:
                    locations.append(block.title())
            
            conn.close()
        except sqlite3.OperationalError as e:
            print(f"[DB ERROR] Could not fetch locations: {e}")
        except Exception as e:
            print(f"[GENERAL ERROR] Location extraction failed: {e}")
        
        return list(set(locations))  # Remove duplicates
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Main method to process user query"""
        intent, entities = self.classify_intent(query)
        
        # Get appropriate response based on intent
        response_data = self._get_response_data(intent, entities)
        
        return {
            'intent': intent,
            'entities': entities,
            'data': response_data,
            'query': query
        }
    
    def _get_response_data(self, intent: str, entities: Dict[str, Any]) -> Any:
        """Fetch relevant data based on intent and entities"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if intent == 'groundwater_status':
                return self._get_groundwater_status(cursor, entities)
            elif intent == 'critical_areas':
                return self._get_critical_areas(cursor)
            elif intent == 'safe_areas':
                return self._get_safe_areas(cursor)
            elif intent == 'water_level':
                return self._get_water_levels(cursor, entities)
            elif intent == 'historical':
                return self._get_historical_data(cursor, entities)
            elif intent == 'recharge':
                return self._get_recharge_data(cursor, entities)
            elif intent == 'extraction':
                return self._get_extraction_data(cursor, entities)
            elif intent == 'help':
                return self._get_help_info()
            else:
                return self._get_general_stats(cursor)
        finally:
            conn.close()
    
    # ---------------- DATA FETCH METHODS ---------------- #
    def _get_groundwater_status(self, cursor, entities):
        """Get groundwater status for specified location"""
        location = entities.get('locations', ['Delhi'])[0] if entities.get('locations') else 'Delhi'
        year = entities.get('years', [2024])[0] if entities.get('years') else 2024
        
        query = """
        SELECT b.block_name, ga.category, ga.stage_of_extraction, 
               ga.water_level_pre_monsoon, ga.annual_recharge_mcm,
               d.district_name, s.state_name
        FROM groundwater_assessment ga
        JOIN blocks b ON ga.block_id = b.block_id
        JOIN districts d ON b.district_id = d.district_id
        JOIN states s ON d.state_id = s.state_id
        WHERE (LOWER(s.state_name) LIKE ? OR LOWER(d.district_name) LIKE ?)
        AND ga.assessment_year = ?
        LIMIT 10
        """
        
        cursor.execute(query, (f'%{location.lower()}%', f'%{location.lower()}%', year))
        results = cursor.fetchall()
        
        return {
            'location': location,
            'year': year,
            'blocks': [
                {
                    'block_name': row[0],
                    'category': row[1],
                    'stage_of_extraction': round(row[2], 2),
                    'water_level': round(row[3], 2),
                    'annual_recharge': round(row[4], 2),
                    'district': row[5],
                    'state': row[6]
                } for row in results
            ]
        }
    
    def _get_critical_areas(self, cursor):
        """Get list of critical and over-exploited areas"""
        query = """
        SELECT b.block_name, d.district_name, s.state_name, 
               ga.category, ga.stage_of_extraction
        FROM groundwater_assessment ga
        JOIN blocks b ON ga.block_id = b.block_id
        JOIN districts d ON b.district_id = d.district_id
        JOIN states s ON d.state_id = s.state_id
        WHERE ga.category IN ('Critical', 'Over-Exploited')
        AND ga.assessment_year = 2024
        ORDER BY ga.stage_of_extraction DESC
        LIMIT 15
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        return {
            'critical_areas': [
                {
                    'block': row[0],
                    'district': row[1],
                    'state': row[2],
                    'category': row[3],
                    'extraction_percentage': round(row[4], 2)
                } for row in results
            ]
        }
    
    def _get_safe_areas(self, cursor):
        """Get list of safe areas"""
        query = """
        SELECT b.block_name, d.district_name, s.state_name, 
               ga.stage_of_extraction, ga.annual_recharge_mcm
        FROM groundwater_assessment ga
        JOIN blocks b ON ga.block_id = b.block_id
        JOIN districts d ON b.district_id = d.district_id
        JOIN states s ON d.state_id = s.state_id
        WHERE ga.category = 'Safe'
        AND ga.assessment_year = 2024
        ORDER BY ga.stage_of_extraction ASC
        LIMIT 15
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        return {
            'safe_areas': [
                {
                    'block': row[0],
                    'district': row[1],
                    'state': row[2],
                    'extraction_percentage': round(row[3], 2),
                    'annual_recharge': round(row[4], 2)
                } for row in results
            ]
        }
    
    def _get_water_levels(self, cursor, entities):
        """Get water level information"""
        location = entities.get('locations', ['Delhi'])[0] if entities.get('locations') else None
        
        if location:
            query = """
            SELECT b.block_name, ga.water_level_pre_monsoon, 
                   ga.water_level_post_monsoon, ga.assessment_year
            FROM groundwater_assessment ga
            JOIN blocks b ON ga.block_id = b.block_id
            JOIN districts d ON b.district_id = d.district_id
            JOIN states s ON d.state_id = s.state_id
            WHERE (LOWER(s.state_name) LIKE ? OR LOWER(d.district_name) LIKE ?)
            AND ga.assessment_year = 2024
            LIMIT 10
            """
            cursor.execute(query, (f'%{location.lower()}%', f'%{location.lower()}%'))
        else:
            query = """
            SELECT AVG(water_level_pre_monsoon), AVG(water_level_post_monsoon)
            FROM groundwater_assessment
            WHERE assessment_year = 2024
            """
            cursor.execute(query)
        
        results = cursor.fetchall()
        
        if location:
            return {
                'location': location,
                'water_levels': [
                    {
                        'block': row[0],
                        'pre_monsoon': round(row[1], 2),
                        'post_monsoon': round(row[2], 2),
                        'year': row[3]
                    } for row in results
                ]
            }
        else:
            return {
                'average_water_levels': {
                    'pre_monsoon': round(results[0][0], 2),
                    'post_monsoon': round(results[0][1], 2)
                }
            }
    
    def _get_historical_data(self, cursor, entities):
        """Get historical groundwater data"""
        years = entities.get('years', [2020, 2021, 2022, 2023, 2024])
        location = entities.get('locations', [])[0] if entities.get('locations') else None
        
        if location:
            query = """
            SELECT ga.assessment_year, AVG(ga.stage_of_extraction), 
                   AVG(ga.water_level_pre_monsoon), COUNT(DISTINCT b.block_id)
            FROM groundwater_assessment ga
            JOIN blocks b ON ga.block_id = b.block_id
            JOIN districts d ON b.district_id = d.district_id
            JOIN states s ON d.state_id = s.state_id
            WHERE (LOWER(s.state_name) LIKE ? OR LOWER(d.district_name) LIKE ?)
            GROUP BY ga.assessment_year
            ORDER BY ga.assessment_year
            """
            cursor.execute(query, (f'%{location.lower()}%', f'%{location.lower()}%'))
        else:
            query = """
            SELECT assessment_year, AVG(stage_of_extraction), 
                   AVG(water_level_pre_monsoon), COUNT(DISTINCT block_id)
            FROM groundwater_assessment
            GROUP BY assessment_year
            ORDER BY assessment_year
            """
            cursor.execute(query)
        
        results = cursor.fetchall()
        
        return {
            'historical_trends': [
                {
                    'year': row[0],
                    'avg_extraction': round(row[1], 2),
                    'avg_water_level': round(row[2], 2),
                    'blocks_assessed': row[3]
                } for row in results
            ],
            'location': location if location else 'All India'
        }
    
    def _get_recharge_data(self, cursor, entities):
        """Get groundwater recharge information"""
        location = entities.get('locations', [])[0] if entities.get('locations') else None
        
        if location:
            query = """
            SELECT b.block_name, ga.annual_recharge_mcm, ga.extractable_resources_mcm
            FROM groundwater_assessment ga
            JOIN blocks b ON ga.block_id = b.block_id
            JOIN districts d ON b.district_id = d.district_id
            JOIN states s ON d.state_id = s.state_id
            WHERE (LOWER(s.state_name) LIKE ? OR LOWER(d.district_name) LIKE ?)
            AND ga.assessment_year = 2024
            LIMIT 10
            """
            cursor.execute(query, (f'%{location.lower()}%', f'%{location.lower()}%'))
        else:
            query = """
            SELECT AVG(annual_recharge_mcm), AVG(extractable_resources_mcm),
                   SUM(annual_recharge_mcm)
            FROM groundwater_assessment
            WHERE assessment_year = 2024
            """
            cursor.execute(query)
        
        results = cursor.fetchall()
        
        if location:
            return {
                'location': location,
                'recharge_data': [
                    {
                        'block': row[0],
                        'annual_recharge': round(row[1], 2),
                        'extractable_resources': round(row[2], 2)
                    } for row in results
                ]
            }
        else:
            return {
                'national_recharge': {
                    'average_annual_recharge': round(results[0][0], 2),
                    'average_extractable': round(results[0][1], 2),
                    'total_recharge': round(results[0][2], 2)
                }
            }
    
    def _get_extraction_data(self, cursor, entities):
        """Get groundwater extraction information"""
        location = entities.get('locations', [])[0] if entities.get('locations') else None
        
        if location:
            query = """
            SELECT b.block_name, ga.total_extraction_mcm, ga.stage_of_extraction, ga.category
            FROM groundwater_assessment ga
            JOIN blocks b ON ga.block_id = b.block_id
            JOIN districts d ON b.district_id = d.district_id
            JOIN states s ON d.state_id = s.state_id
            WHERE (LOWER(s.state_name) LIKE ? OR LOWER(d.district_name) LIKE ?)
            AND ga.assessment_year = 2024
            LIMIT 10
            """
            cursor.execute(query, (f'%{location.lower()}%', f'%{location.lower()}%'))
        else:
            query = """
            SELECT AVG(total_extraction_mcm), AVG(stage_of_extraction),
                   SUM(total_extraction_mcm)
            FROM groundwater_assessment
            WHERE assessment_year = 2024
            """
            cursor.execute(query)
        
        results = cursor.fetchall()
        
        if location:
            return {
                'location': location,
                'extraction_data': [
                    {
                        'block': row[0],
                        'total_extraction': round(row[1], 2),
                        'extraction_stage': round(row[2], 2),
                        'category': row[3]
                    } for row in results
                ]
            }
        else:
            return {
                'national_extraction': {
                    'average_extraction': round(results[0][0], 2),
                    'average_stage': round(results[0][1], 2),
                    'total_extraction': round(results[0][2], 2)
                }
            }
    
    def _get_general_stats(self, cursor):
        """Get general statistics about groundwater"""
        query = """
        SELECT COUNT(DISTINCT s.state_id), COUNT(DISTINCT d.district_id), 
               COUNT(DISTINCT b.block_id), AVG(ga.stage_of_extraction)
        FROM groundwater_assessment ga
        JOIN blocks b ON ga.block_id = b.block_id
        JOIN districts d ON b.district_id = d.district_id
        JOIN states s ON d.state_id = s.state_id
        WHERE ga.assessment_year = 2024
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        return {
            'general_stats': {
                'states_covered': result[0],
                'districts_covered': result[1],
                'blocks_covered': result[2],
                'average_extraction_stage': round(result[3], 2)
            }
        }
    
    def _get_help_info(self):
        """Provide help information about chatbot capabilities"""
        return {
            'help': [
                "You can ask about groundwater status in any state/district/block.",
                "Examples:",
                "- What is the groundwater status in Karnataka?",
                "- Show critical areas in Tamil Nadu",
                "- What is the average water level in Delhi?",
                "- Give me historical trends for Punjab",
                "- Compare extraction between states",
                "- List safe areas in Maharashtra",
                "- Show recharge and extraction rates"
            ]
        }
