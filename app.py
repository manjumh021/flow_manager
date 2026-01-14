"""
Flask REST API for Flow Manager microservice.
Provides endpoints for flow execution, status checking, and validation.
"""

from flask import Flask, request, jsonify
from typing import Dict, Any
import logging

from flow_engine import FlowParser, FlowOrchestrator
from models import FlowStatus
import sample_tasks  # Import to register tasks

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Global orchestrator instance
orchestrator = FlowOrchestrator()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Flow Manager"
    }), 200


@app.route('/flow/execute', methods=['POST'])
def execute_flow():
    """
    Execute a flow from JSON definition.
    
    Request Body:
        JSON flow definition
        
    Returns:
        Execution state with results
    """
    try:
        flow_json = request.get_json()
        
        if not flow_json:
            return jsonify({
                "error": "No JSON data provided"
            }), 400
        
        # Parse flow
        logger.info("Parsing flow definition...")
        flow = FlowParser.parse(flow_json)
        
        # Execute flow
        logger.info(f"Executing flow: {flow.name} (ID: {flow.id})")
        execution_state = orchestrator.execute_flow(flow)
        
        # Return execution results
        result = execution_state.to_dict()
        
        status_code = 200 if execution_state.status == FlowStatus.COMPLETED else 500
        
        return jsonify(result), status_code
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({
            "error": "Invalid flow definition",
            "details": str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Error executing flow: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500


@app.route('/flow/status/<execution_id>', methods=['GET'])
def get_flow_status(execution_id: str):
    """
    Get the status of a flow execution.
    
    Args:
        execution_id: UUID of the flow execution
        
    Returns:
        Execution state
    """
    try:
        state = orchestrator.get_execution_state(execution_id)
        
        if not state:
            return jsonify({
                "error": f"Execution ID '{execution_id}' not found"
            }), 404
        
        return jsonify(state.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Error getting flow status: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500


@app.route('/flow/validate', methods=['POST'])
def validate_flow():
    """
    Validate a flow JSON definition without executing it.
    
    Request Body:
        JSON flow definition
        
    Returns:
        Validation result
    """
    try:
        flow_json = request.get_json()
        
        if not flow_json:
            return jsonify({
                "error": "No JSON data provided"
            }), 400
        
        # Parse and validate flow
        flow = FlowParser.parse(flow_json)
        
        return jsonify({
            "valid": True,
            "flow": flow.to_dict(),
            "message": "Flow definition is valid"
        }), 200
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({
            "valid": False,
            "error": str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Error validating flow: {str(e)}")
        return jsonify({
            "valid": False,
            "error": str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "error": "Endpoint not found"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        "error": "Internal server error"
    }), 500


if __name__ == '__main__':
    logger.info("Starting Flow Manager microservice...")
    logger.info("Available endpoints:")
    logger.info("  GET  /health")
    logger.info("  POST /flow/execute")
    logger.info("  GET  /flow/status/<execution_id>")
    logger.info("  POST /flow/validate")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
