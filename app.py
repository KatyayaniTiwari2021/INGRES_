from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from datetime import datetime
from query_processor import QueryProcessor
import traceback   # ✅ Added for debugging

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize the query processor
query_processor = QueryProcessor()

# Store chat history (in production, use a proper database)
chat_history = []


def format_response(query_result):
    """Format the query result into a human-readable response"""
    intent = query_result['intent']
    data = query_result['data']

    response = ""

    if intent == 'groundwater_status':
        location = data.get('location', 'Unknown')
        year = data.get('year', 2024)
        blocks = data.get('blocks', [])

        if blocks:
            response = f"📍 **Groundwater Status for {location} ({year})**\n\n"
            for block in blocks[:5]:  # Show top 5 blocks
                status_emoji = "🟢" if block['category'] == 'Safe' else "🟡" if block['category'] == 'Semi-Critical' else "🔴"
                response += f"{status_emoji} **{block['block_name']}**\n"
                response += f"   • Category: {block['category']}\n"
                response += f"   • Extraction: {block['stage_of_extraction']}%\n"
                response += f"   • Water Level: {block['water_level']}m below ground\n"
                response += f"   • Annual Recharge: {block['annual_recharge']} MCM\n\n"
        else:
            response = f"No data found for {location}. Please try another location."

    elif intent == 'critical_areas':
        areas = data.get('critical_areas', [])
        if areas:
            response = "🚨 **Critical and Over-Exploited Areas**\n\n"
            for area in areas[:10]:
                response += f"🔴 **{area['block']}**, {area['district']}, {area['state']}\n"
                response += f"   • Status: {area['category']}\n"
                response += f"   • Extraction: {area['extraction_percentage']}%\n\n"
        else:
            response = "No critical areas found in the current assessment."

    elif intent == 'safe_areas':
        areas = data.get('safe_areas', [])
        if areas:
            response = "✅ **Safe Groundwater Areas**\n\n"
            for area in areas[:10]:
                response += f"🟢 **{area['block']}**, {area['district']}, {area['state']}\n"
                response += f"   • Extraction: {area['extraction_percentage']}%\n"
                response += f"   • Annual Recharge: {area['annual_recharge']} MCM\n\n"
        else:
            response = "No safe areas data available."

    elif intent == 'water_level':
        if 'location' in data:
            location = data['location']
            levels = data.get('water_levels', [])
            if levels:
                response = f"💧 **Water Levels in {location}**\n\n"
                for level in levels[:5]:
                    response += f"📍 **{level['block']}**\n"
                    response += f"   • Pre-monsoon: {level['pre_monsoon']}m\n"
                    response += f"   • Post-monsoon: {level['post_monsoon']}m\n\n"
            else:
                response = f"No water level data found for {location}."
        else:
            avg_levels = data.get('average_water_levels', {})
            response = "💧 **National Average Water Levels (2024)**\n\n"
            response += f"• Pre-monsoon: {avg_levels.get('pre_monsoon', 'N/A')}m\n"
            response += f"• Post-monsoon: {avg_levels.get('post_monsoon', 'N/A')}m\n"

    elif intent == 'historical':
        location = data.get('location', 'All India')
        trends = data.get('historical_trends', [])
        if trends:
            response = f"📊 **Historical Trends for {location}**\n\n"
            for trend in trends:
                response += f"**Year {trend['year']}**\n"
                response += f"   • Avg Extraction: {trend['avg_extraction']}%\n"
                response += f"   • Avg Water Level: {trend['avg_water_level']}m\n"
                response += f"   • Blocks Assessed: {trend['blocks_assessed']}\n\n"
        else:
            response = "No historical data available."

    elif intent == 'recharge':
        if 'location' in data:
            location = data['location']
            recharge_data = data.get('recharge_data', [])
            if recharge_data:
                response = f"♻️ **Groundwater Recharge in {location}**\n\n"
                for item in recharge_data[:5]:
                    response += f"📍 **{item['block']}**\n"
                    response += f"   • Annual Recharge: {item['annual_recharge']} MCM\n"
                    response += f"   • Extractable: {item['extractable_resources']} MCM\n\n"
            else:
                response = f"No recharge data found for {location}."
        else:
            national = data.get('national_recharge', {})
            response = "♻️ **National Groundwater Recharge Statistics**\n\n"
            response += f"• Average Annual Recharge: {national.get('average_annual_recharge', 'N/A')} MCM\n"
            response += f"• Average Extractable: {national.get('average_extractable', 'N/A')} MCM\n"
            response += f"• Total Recharge: {national.get('total_recharge', 'N/A')} MCM\n"

    elif intent == 'extraction':
        if 'location' in data:
            location = data['location']
            extraction_data = data.get('extraction_data', [])
            if extraction_data:
                response = f"⛏️ **Groundwater Extraction in {location}**\n\n"
                for item in extraction_data[:5]:
                    status_emoji = "🟢" if item['category'] == 'Safe' else "🟡" if item['category'] == 'Semi-Critical' else "🔴"
                    response += f"{status_emoji} **{item['block']}**\n"
                    response += f"   • Total Extraction: {item['total_extraction']} MCM\n"
                    response += f"   • Stage: {item['extraction_stage']}%\n"
                    response += f"   • Category: {item['category']}\n\n"
            else:
                response = f"No extraction data found for {location}."
        else:
            national = data.get('national_extraction', {})
            response = "⛏️ **National Groundwater Extraction Statistics**\n\n"
            response += f"• Average Extraction: {national.get('average_extraction', 'N/A')} MCM\n"
            response += f"• Average Stage: {national.get('average_stage', 'N/A')}%\n"
            response += f"• Total Extraction: {national.get('total_extraction', 'N/A')} MCM\n"

    elif intent == 'help':
        capabilities = data.get('capabilities', [])
        samples = data.get('sample_queries', [])
        response = "🤖 **INGRES ChatBot - How Can I Help?**\n\n"
        response += "**I can help you with:**\n"
        for cap in capabilities:
            response += f"• {cap}\n"
        response += "\n**Try asking me:**\n"
        for sample in samples[:5]:
            response += f"• \"{sample}\"\n"

    else:  # General stats
        coverage = data.get('coverage', {})
        distribution = data.get('category_distribution', {})
        response = "📊 **INGRES Database Overview**\n\n"
        response += "**Coverage:**\n"
        response += f"• States: {coverage.get('states', 0)}\n"
        response += f"• Districts: {coverage.get('districts', 0)}\n"
        response += f"• Blocks: {coverage.get('blocks', 0)}\n\n"
        response += "**2024 Assessment Distribution:**\n"
        for category, count in distribution.items():
            emoji = "🟢" if category == 'Safe' else "🟡" if category == 'Semi-Critical' else "🟠" if category == 'Critical' else "🔴"
            response += f"{emoji} {category}: {count} blocks\n"

    return response


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()   # ✅ safer than request.json
        user_message = data.get('message', '')

        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        # Process the query
        query_result = query_processor.process_query(user_message)

        # Format the response
        bot_response = format_response(query_result)

        # Store in chat history
        chat_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'bot_response': bot_response,
            'intent': query_result['intent'],
            'entities': query_result.get('entities', {})
        }
        chat_history.append(chat_entry)

        return jsonify({
            'response': bot_response,
            'intent': query_result['intent'],
            'entities': query_result.get('entities', {}),
            'timestamp': chat_entry['timestamp']
        })

    except Exception as e:
        print("❌ Error in /api/chat:", e)
        traceback.print_exc()   # ✅ show full error in terminal
        return jsonify({'error': str(e)}), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get chat history"""
    return jsonify({'history': chat_history[-50:]})  # Return last 50 messages


@app.route('/api/clear', methods=['POST'])
def clear_history():
    """Clear chat history"""
    chat_history.clear()   # ✅ instead of reassigning list
    return jsonify({'message': 'Chat history cleared'})


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'INGRES ChatBot API'})


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        # Get general stats using the query processor
        result = query_processor.process_query("show me statistics")
        return jsonify(result['data'])
    except Exception as e:
        print("❌ Error in /api/stats:", e)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route("/")
def home():
    return {"message": "INGRES Chatbot Backend is Running! Use /api/chat to talk."}


if __name__ == '__main__':
    print("🚀 INGRES ChatBot Backend Starting...")
    print("📍 API running on http://localhost:5000")
    print("💡 Endpoints:")
    print("   GET  / - Home route")   # ✅ Added for consistency
    print("   POST /api/chat - Send chat messages")
    print("   GET /api/history - Get chat history")
    print("   POST /api/clear - Clear chat history")
    print("   GET /api/health - Health check")
    print("   GET /api/stats - Get database statistics")
    app.run(debug=True, port=5000)
