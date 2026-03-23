"""
DAP Report Workflow - Daily Activity Performance Analysis

This workflow generates a comprehensive Daily Activity Performance (DAP) report
based on a user-specified date. It retrieves relevant data, performs time-series
analysis, and flags any issues requiring analyst attention.

Execution is BPMN-only; see currentVersion/bpmn-bindings.yaml and the BPMN engine.
Handlers take (self, state) and read/write state.
"""

import importlib.util
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from pathlib import Path


def _load_run_agent() -> Any:
    """Load ``run_agent`` from ``agent_ui/agent_runner.py`` without ``import agent_ui.*`` (avoids inner/outer package name clash when ``sys.path`` includes ``agent_ui/``)."""
    repo_root = Path(__file__).resolve().parents[2]
    runner_path = repo_root / "agent_ui" / "agent_runner.py"
    spec = importlib.util.spec_from_file_location("beeai_agent_runner", runner_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load agent_runner from {runner_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.run_agent

from pydantic import BaseModel, Field

# BPMN engine only needs an executor with handler methods; no need to inherit beeai_framework.Workflow
# (its __init__ expects schema, name, not workflow_id/description/category)

# Local status constants (beeai_framework.workflows does not export WorkflowStatus)
class WorkflowStatus:
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


# Local task types (beeai_framework.tasks not in installed package)
class TaskPriority(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class Task:
    """Minimal task model for analyst task creation."""
    title: str
    description: str
    task_type: str
    priority: TaskPriority
    assigned_to: str
    workflow_id: str
    workflow_instance_id: Optional[str]
    metadata: Dict[str, Any]


def _get_agent(agent_id: str):
    """
    Return a callable that runs the agent via agent_runner.
    Maps workflow agent ids to agents.yaml ids (e.g. gres_agent -> gres).
    """
    agent_map = {"gres_agent": "gres"}
    resolved_id = agent_map.get(agent_id, agent_id)

    class _AgentAdapter:
        def __init__(self, aid: str):
            self._agent_id = aid

        async def process(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
            try:
                run_agent = _load_run_agent()
                response_text, metadata = await run_agent(
                    prompt=query,
                    agent_type=self._agent_id,
                    context_data=context,
                )
                return {"status": "success", "data": {"text": response_text, "metadata": metadata}}
            except Exception as e:
                return {"status": "error", "message": str(e), "data": None}

    return _AgentAdapter(resolved_id)


logger = logging.getLogger(__name__)


class DAPReportState(BaseModel):
    """State for the DAP Report workflow (BPMN engine)."""

    report_date: str = Field(description="Report date YYYY-MM-DD")
    lookback_days: int = Field(default=30, description="Days of history for time-series")
    user_id: str = Field(default="system", description="User requesting the report")

    workflow_steps: List[str] = Field(default_factory=list)

    dap_data: Optional[Dict[str, Any]] = None
    time_series_data: Optional[List[Dict[str, Any]]] = None
    trends: Optional[Dict[str, Any]] = None
    analysis_results: Optional[Dict[str, Any]] = None
    issues_found: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = {"extra": "allow"}


class DAPReportWorkflow:
    """
    Daily Activity Performance Report Workflow
    
    Generates comprehensive DAP reports with automated analysis and issue detection.
    Creates analyst tasks when performance anomalies or issues are detected.
    BPMN engine uses this as executor (handlers: retrieve_data, create_time_series, create_analysis).
    """

    workflow_id = "dap_report"
    name = "DAP Report"

    def __init__(self, run_id: Optional[str] = None):
        """Initialize the DAP Report workflow."""
        self.run_id = run_id
        self.dap_data: Optional[Dict[str, Any]] = None
        self.time_series_data: Optional[List[Dict[str, Any]]] = None
        self.analysis_results: Optional[Dict[str, Any]] = None
        self.issues_found: List[Dict[str, Any]] = []

    def _context_from_state(self, state: DAPReportState) -> Dict[str, Any]:
        """Build context dict from state for existing step methods."""
        return {
            "report_date": state.report_date,
            "lookback_days": state.lookback_days,
            "user_id": state.user_id,
            "include_comparison": True,
        }

    async def retrieve_data(self, state: DAPReportState) -> Optional[str]:
        """BPMN handler: validate input and retrieve DAP data."""
        context = self._context_from_state(state)
        validation = await self.validate_input(context)
        if validation.get("status") != WorkflowStatus.SUCCESS:
            raise RuntimeError(validation.get("message", "Validation failed"))
        result = await self.retrieve_dap_data(context)
        if result.get("status") != WorkflowStatus.SUCCESS:
            raise RuntimeError(result.get("message", "Retrieve failed"))
        state.dap_data = self.dap_data
        return "create_time_series"

    async def create_time_series(self, state: DAPReportState) -> Optional[str]:
        """BPMN handler: build time-series and trends."""
        context = self._context_from_state(state)
        self.dap_data = state.dap_data
        result = await self.create_time_series_from_context(context)
        if result.get("status") != WorkflowStatus.SUCCESS:
            raise RuntimeError(result.get("message", "Time-series failed"))
        state.time_series_data = self.time_series_data
        state.trends = getattr(self, "_last_trends", None)
        return "create_analysis"

    async def create_analysis(self, state: DAPReportState) -> Optional[str]:
        """BPMN handler: generate analysis and check/flag issues."""
        context = self._context_from_state(state)
        self.dap_data = state.dap_data
        self.time_series_data = state.time_series_data or []
        result = await self.generate_analysis(context)
        if result.get("status") != WorkflowStatus.SUCCESS:
            raise RuntimeError(result.get("message", "Analysis failed"))
        issue_result = await self.check_and_flag_issues(context)
        state.analysis_results = self.analysis_results
        state.issues_found = self.issues_found
        return None

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the DAP report workflow.
        
        Args:
            context: Workflow context containing:
                - report_date: Date for the DAP report (string, format: YYYY-MM-DD)
                - user_id: ID of user requesting the report
                - include_comparison: Optional, include historical comparison (default: True)
                - lookback_days: Optional, days to include in time-series (default: 30)
        
        Returns:
            Dictionary containing:
                - status: Workflow execution status
                - message: Human-readable result message
                - data: Report data and analysis results
                - tasks_created: List of task IDs if issues were flagged
        """
        try:
            logger.info(f"Starting DAP Report workflow for date: {context.get('report_date')}")
            
            # Step 1: Validate input date
            validation_result = await self.validate_input(context)
            if validation_result['status'] != WorkflowStatus.SUCCESS:
                return validation_result
            
            # Step 2: Retrieve DAP data
            retrieval_result = await self.retrieve_dap_data(context)
            if retrieval_result['status'] != WorkflowStatus.SUCCESS:
                return retrieval_result
            
            # Step 3: Create time-series analysis
            timeseries_result = await self.create_time_series_from_context(context)
            if timeseries_result['status'] != WorkflowStatus.SUCCESS:
                return timeseries_result
            
            # Step 4: Generate analysis
            analysis_result = await self.generate_analysis(context)
            if analysis_result['status'] != WorkflowStatus.SUCCESS:
                return analysis_result
            
            # Step 5: Check for issues and create tasks if needed
            issue_result = await self.check_and_flag_issues(context)
            
            # Compile final report
            report_data = {
                'report_date': context.get('report_date'),
                'generated_at': datetime.utcnow().isoformat(),
                'dap_data': self.dap_data,
                'time_series': self.time_series_data,
                'analysis': self.analysis_results,
                'issues': self.issues_found,
                'tasks_created': issue_result.get('tasks_created', [])
            }
            
            logger.info(f"DAP Report workflow completed successfully. Issues found: {len(self.issues_found)}")
            
            return {
                'status': WorkflowStatus.SUCCESS,
                'message': f"DAP report generated successfully for {context.get('report_date')}. "
                          f"{len(self.issues_found)} issue(s) detected.",
                'data': report_data,
                'tasks_created': issue_result.get('tasks_created', [])
            }
            
        except Exception as e:
            logger.error(f"DAP Report workflow failed: {str(e)}", exc_info=True)
            return {
                'status': WorkflowStatus.FAILED,
                'message': f"DAP report generation failed: {str(e)}",
                'data': None,
                'error': str(e)
            }
    
    async def validate_input(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the input date and workflow parameters.
        
        Args:
            context: Workflow context with report_date
            
        Returns:
            Validation result with status and message
        """
        try:
            logger.info("Step 1: Validating input parameters")
            
            # Check if report_date is provided
            report_date_str = context.get('report_date')
            if not report_date_str:
                return {
                    'status': WorkflowStatus.FAILED,
                    'message': "Missing required parameter: report_date",
                    'data': None
                }
            
            # Validate date format
            try:
                report_date = datetime.strptime(report_date_str, '%Y-%m-%d')
            except ValueError:
                return {
                    'status': WorkflowStatus.FAILED,
                    'message': f"Invalid date format: {report_date_str}. Expected format: YYYY-MM-DD",
                    'data': None
                }
            
            # Check if date is not in the future
            if report_date.date() > datetime.utcnow().date():
                return {
                    'status': WorkflowStatus.FAILED,
                    'message': f"Report date cannot be in the future: {report_date_str}",
                    'data': None
                }
            
            # Check if date is not too old (e.g., more than 1 year)
            one_year_ago = datetime.utcnow() - timedelta(days=365)
            if report_date < one_year_ago:
                logger.warning(f"Report date is more than 1 year old: {report_date_str}")
            
            # Set defaults for optional parameters
            context.setdefault('include_comparison', True)
            context.setdefault('lookback_days', 30)
            context.setdefault('user_id', 'system')
            
            # Validate lookback_days
            lookback_days = context.get('lookback_days', 30)
            if not isinstance(lookback_days, int) or lookback_days < 1 or lookback_days > 365:
                logger.warning(f"Invalid lookback_days: {lookback_days}. Using default: 30")
                context['lookback_days'] = 30
            
            logger.info(f"Input validation successful for date: {report_date_str}")
            
            return {
                'status': WorkflowStatus.SUCCESS,
                'message': "Input validation successful",
                'data': {
                    'validated_date': report_date.isoformat(),
                    'lookback_days': context['lookback_days']
                }
            }
            
        except Exception as e:
            logger.error(f"Input validation failed: {str(e)}", exc_info=True)
            return {
                'status': WorkflowStatus.FAILED,
                'message': f"Input validation error: {str(e)}",
                'data': None
            }
    
    async def retrieve_dap_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve DAP data for the specified date using the GRES Agent.
        
        Args:
            context: Workflow context with validated report_date
            
        Returns:
            Retrieval result with DAP data
        """
        try:
            logger.info("Step 2: Retrieving DAP data")
            
            report_date = context.get('report_date')
            
            # Get GRES agent (via agent_runner)
            gres_agent = _get_agent('gres_agent')
            if not gres_agent:
                return {
                    'status': WorkflowStatus.FAILED,
                    'message': "GRES Agent not available",
                    'data': None
                }
            
            # Query for DAP data
            query = f"""
            Retrieve Daily Activity Performance (DAP) data for {report_date}.
            Include the following metrics:
            - Total auctions active
            - New auctions created
            - Auctions closed
            - Total bids placed
            - New bidder registrations
            - Property views
            - Unique visitors
            - Average bid amount
            - Total revenue
            - Compliance checks performed
            - Failed compliance checks
            - Agent activities
            - System performance metrics
            
            Return comprehensive data for analysis.
            """
            
            # Execute agent query
            agent_response = await gres_agent.process(query, context)
            
            if not agent_response or agent_response.get('status') == 'error':
                return {
                    'status': WorkflowStatus.FAILED,
                    'message': f"Failed to retrieve DAP data: {agent_response.get('message', 'Unknown error')}",
                    'data': None
                }
            
            # Extract and structure DAP data
            self.dap_data = {
                'date': report_date,
                'metrics': {
                    'auctions': {
                        'active': agent_response.get('data', {}).get('auctions_active', 0),
                        'new': agent_response.get('data', {}).get('auctions_new', 0),
                        'closed': agent_response.get('data', {}).get('auctions_closed', 0)
                    },
                    'bidding': {
                        'total_bids': agent_response.get('data', {}).get('total_bids', 0),
                        'new_bidders': agent_response.get('data', {}).get('new_bidders', 0),
                        'average_bid': agent_response.get('data', {}).get('average_bid', 0)
                    },
                    'engagement': {
                        'property_views': agent_response.get('data', {}).get('property_views', 0),
                        'unique_visitors': agent_response.get('data', {}).get('unique_visitors', 0)
                    },
                    'revenue': {
                        'total': agent_response.get('data', {}).get('total_revenue', 0)
                    },
                    'compliance': {
                        'checks_performed': agent_response.get('data', {}).get('compliance_checks', 0),
                        'checks_failed': agent_response.get('data', {}).get('compliance_failures', 0)
                    },
                    'system': {
                        'uptime_percentage': agent_response.get('data', {}).get('uptime', 99.9),
                        'avg_response_time': agent_response.get('data', {}).get('response_time', 0)
                    }
                },
                'raw_data': agent_response.get('data', {})
            }
            
            logger.info(f"Successfully retrieved DAP data for {report_date}")
            
            return {
                'status': WorkflowStatus.SUCCESS,
                'message': "DAP data retrieved successfully",
                'data': self.dap_data
            }
            
        except Exception as e:
            logger.error(f"DAP data retrieval failed: {str(e)}", exc_info=True)
            return {
                'status': WorkflowStatus.FAILED,
                'message': f"Data retrieval error: {str(e)}",
                'data': None
            }
    
    async def create_time_series_from_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create time-series data for trend analysis (called by BPMN handler or execute()).
        
        Args:
            context: Workflow context with lookback_days parameter
            
        Returns:
            Time-series data result
        """
        try:
            logger.info("Step 3: Creating time-series analysis")
            
            report_date = datetime.strptime(context.get('report_date'), '%Y-%m-%d')
            lookback_days = context.get('lookback_days', 30)
            
            # Get GRES agent (via agent_runner)
            gres_agent = _get_agent('gres_agent')
            if not gres_agent:
                return {
                    'status': WorkflowStatus.FAILED,
                    'message': "GRES Agent not available for time-series data",
                    'data': None
                }
            
            # Calculate date range
            start_date = report_date - timedelta(days=lookback_days)
            
            # Query for historical data
            query = f"""
            Retrieve daily metrics from {start_date.strftime('%Y-%m-%d')} to {report_date.strftime('%Y-%m-%d')}.
            Include: auctions, bids, bidders, revenue, compliance checks.
            Format as time-series data for trend analysis.
            """
            
            agent_response = await gres_agent.process(query, context)
            
            if not agent_response or agent_response.get('status') == 'error':
                logger.warning("Failed to retrieve complete time-series data, using current data only")
                # Fallback: create minimal time-series with current data
                self.time_series_data = [{
                    'date': context.get('report_date'),
                    'metrics': self.dap_data.get('metrics', {})
                }]
            else:
                # Extract time-series data
                historical_data = agent_response.get('data', {}).get('time_series', [])
                
                # Ensure current date data is included
                self.time_series_data = historical_data
                if not any(d.get('date') == context.get('report_date') for d in self.time_series_data):
                    self.time_series_data.append({
                        'date': context.get('report_date'),
                        'metrics': self.dap_data.get('metrics', {})
                    })
            
            # Calculate trends
            trends = self._calculate_trends(self.time_series_data)
            self._last_trends = trends

            logger.info(f"Time-series created with {len(self.time_series_data)} data points")

            return {
                'status': WorkflowStatus.SUCCESS,
                'message': f"Time-series analysis created ({len(self.time_series_data)} days)",
                'data': {
                    'time_series': self.time_series_data,
                    'trends': trends
                }
            }
            
        except Exception as e:
            logger.error(f"Time-series creation failed: {str(e)}", exc_info=True)
            return {
                'status': WorkflowStatus.FAILED,
                'message': f"Time-series creation error: {str(e)}",
                'data': None
            }
    
    def _calculate_trends(self, time_series: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate trends from time-series data.
        
        Args:
            time_series: List of daily metrics
            
        Returns:
            Dictionary of calculated trends
        """
        if len(time_series) < 2:
            return {'status': 'insufficient_data'}
        
        try:
            # Get first and last data points
            first_day = time_series[0]
            last_day = time_series[-1]
            
            # Calculate percentage changes
            trends = {}
            
            # Auction trends
            first_auctions = first_day.get('metrics', {}).get('auctions', {}).get('active', 0)
            last_auctions = last_day.get('metrics', {}).get('auctions', {}).get('active', 0)
            trends['auctions_change'] = self._calculate_percentage_change(first_auctions, last_auctions)
            
            # Bidding trends
            first_bids = first_day.get('metrics', {}).get('bidding', {}).get('total_bids', 0)
            last_bids = last_day.get('metrics', {}).get('bidding', {}).get('total_bids', 0)
            trends['bids_change'] = self._calculate_percentage_change(first_bids, last_bids)
            
            # Revenue trends
            first_revenue = first_day.get('metrics', {}).get('revenue', {}).get('total', 0)
            last_revenue = last_day.get('metrics', {}).get('revenue', {}).get('total', 0)
            trends['revenue_change'] = self._calculate_percentage_change(first_revenue, last_revenue)
            
            # Compliance trends
            first_compliance = first_day.get('metrics', {}).get('compliance', {}).get('checks_failed', 0)
            last_compliance = last_day.get('metrics', {}).get('compliance', {}).get('checks_failed', 0)
            trends['compliance_failures_change'] = self._calculate_percentage_change(first_compliance, last_compliance)
            
            return trends
            
        except Exception as e:
            logger.error(f"Trend calculation error: {str(e)}")
            return {'status': 'calculation_error', 'error': str(e)}
    
    def _calculate_percentage_change(self, old_value: float, new_value: float) -> Dict[str, Any]:
        """Calculate percentage change between two values."""
        if old_value == 0:
            if new_value == 0:
                return {'change': 0, 'percentage': 0, 'direction': 'stable'}
            else:
                return {'change': new_value, 'percentage': 100, 'direction': 'up'}
        
        change = new_value - old_value
        percentage = (change / old_value) * 100
        direction = 'up' if change > 0 else 'down' if change < 0 else 'stable'
        
        return {
            'change': round(change, 2),
            'percentage': round(percentage, 2),
            'direction': direction
        }
    
    async def generate_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive analysis of DAP data and trends.
        
        Args:
            context: Workflow context
            
        Returns:
            Analysis results
        """
        try:
            logger.info("Step 4: Generating performance analysis")
            
            # Get GRES agent (via agent_runner)
            gres_agent = _get_agent('gres_agent')
            if not gres_agent:
                return {
                    'status': WorkflowStatus.FAILED,
                    'message': "GRES Agent not available for analysis",
                    'data': None
                }
            
            # Prepare analysis query
            analysis_query = f"""
            Analyze the following Daily Activity Performance data for {context.get('report_date')}:
            
            Current Metrics:
            {self._format_metrics_for_analysis(self.dap_data.get('metrics', {}))}
            
            Time-Series Trends:
            {self._format_trends_for_analysis(self.time_series_data)}
            
            Provide a comprehensive analysis including:
            1. Overall performance assessment
            2. Key highlights and achievements
            3. Areas of concern or decline
            4. Anomalies or unusual patterns
            5. Recommendations for improvement
            6. Comparison to historical averages
            7. Risk factors or issues requiring attention
            
            Flag any critical issues that require immediate analyst attention.
            """
            
            # Execute analysis
            agent_response = await gres_agent.process(analysis_query, context)
            
            if not agent_response or agent_response.get('status') == 'error':
                return {
                    'status': WorkflowStatus.FAILED,
                    'message': f"Analysis generation failed: {agent_response.get('message', 'Unknown error')}",
                    'data': None
                }
            
            # Structure analysis results
            self.analysis_results = {
                'summary': agent_response.get('data', {}).get('summary', ''),
                'performance_score': agent_response.get('data', {}).get('score', 0),
                'highlights': agent_response.get('data', {}).get('highlights', []),
                'concerns': agent_response.get('data', {}).get('concerns', []),
                'anomalies': agent_response.get('data', {}).get('anomalies', []),
                'recommendations': agent_response.get('data', {}).get('recommendations', []),
                'risk_level': agent_response.get('data', {}).get('risk_level', 'low'),
                'detailed_analysis': agent_response.get('data', {}).get('detailed_analysis', '')
            }
            
            logger.info(f"Analysis generated with risk level: {self.analysis_results.get('risk_level')}")
            
            return {
                'status': WorkflowStatus.SUCCESS,
                'message': "Performance analysis completed",
                'data': self.analysis_results
            }
            
        except Exception as e:
            logger.error(f"Analysis generation failed: {str(e)}", exc_info=True)
            return {
                'status': WorkflowStatus.FAILED,
                'message': f"Analysis generation error: {str(e)}",
                'data': None
            }
    
    def _format_metrics_for_analysis(self, metrics: Dict[str, Any]) -> str:
        """Format metrics dictionary for analysis query."""
        formatted = []
        for category, values in metrics.items():
            formatted.append(f"\n{category.upper()}:")
            for key, value in values.items():
                formatted.append(f"  - {key}: {value}")
        return '\n'.join(formatted)
    
    def _format_trends_for_analysis(self, time_series: List[Dict[str, Any]]) -> str:
        """Format time-series data for analysis query."""
        if not time_series or len(time_series) < 2:
            return "Insufficient data for trend analysis"
        
        return f"Data points: {len(time_series)} days\nDate range: {time_series[0].get('date')} to {time_series[-1].get('date')}"
    
    async def check_and_flag_issues(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for issues in the analysis and create analyst tasks if needed.
        
        Args:
            context: Workflow context with user_id
            
        Returns:
            Result with created task IDs
        """
        try:
            logger.info("Step 5: Checking for issues and creating tasks")
            
            tasks_created = []
            
            # Check risk level
            risk_level = self.analysis_results.get('risk_level', 'low')
            
            # Check for concerns
            concerns = self.analysis_results.get('concerns', [])
            
            # Check for anomalies
            anomalies = self.analysis_results.get('anomalies', [])
            
            # Determine if issues require analyst attention
            requires_attention = (
                risk_level in ['high', 'critical'] or
                len(concerns) > 0 or
                len(anomalies) > 0
            )
            
            if requires_attention:
                # Compile issues
                self.issues_found = []
                
                if risk_level in ['high', 'critical']:
                    self.issues_found.append({
                        'type': 'risk_level',
                        'severity': risk_level,
                        'description': f"High risk level detected: {risk_level}",
                        'requires_action': True
                    })
                
                for concern in concerns:
                    self.issues_found.append({
                        'type': 'concern',
                        'severity': 'medium',
                        'description': concern,
                        'requires_action': True
                    })
                
                for anomaly in anomalies:
                    self.issues_found.append({
                        'type': 'anomaly',
                        'severity': 'high',
                        'description': anomaly,
                        'requires_action': True
                    })
                
                # Create analyst task
                task = await self._create_analyst_task(context)
                if task:
                    tasks_created.append(task.get('task_id'))
                    logger.info(f"Created analyst task: {task.get('task_id')}")
                
                # Create user toast notification
                await self._create_user_toast(context, len(self.issues_found))
            
            logger.info(f"Issue check completed. {len(self.issues_found)} issue(s) found, {len(tasks_created)} task(s) created")
            
            return {
                'status': WorkflowStatus.SUCCESS,
                'message': f"{len(self.issues_found)} issue(s) detected",
                'data': {
                    'issues': self.issues_found,
                    'requires_attention': requires_attention
                },
                'tasks_created': tasks_created
            }
            
        except Exception as e:
            logger.error(f"Issue checking failed: {str(e)}", exc_info=True)
            return {
                'status': WorkflowStatus.SUCCESS,  # Don't fail workflow if task creation fails
                'message': f"Issue checking completed with errors: {str(e)}",
                'data': {'issues': self.issues_found},
                'tasks_created': []
            }
    
    async def _create_analyst_task(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a task for analyst to review DAP report issues.
        
        Args:
            context: Workflow context
            
        Returns:
            Created task information
        """
        try:
            # Determine priority based on risk level
            risk_level = self.analysis_results.get('risk_level', 'low')
            priority_map = {
                'critical': TaskPriority.URGENT,
                'high': TaskPriority.HIGH,
                'medium': TaskPriority.NORMAL,
                'low': TaskPriority.LOW
            }
            priority = priority_map.get(risk_level, TaskPriority.NORMAL)
            
            # Create task description
            task_description = f"""
# DAP Report Issue Review Required

**Report Date:** {context.get('report_date')}
**Risk Level:** {risk_level.upper()}
**Issues Found:** {len(self.issues_found)}

## Issues Detected:

"""
            for idx, issue in enumerate(self.issues_found, 1):
                task_description += f"{idx}. **{issue['type'].upper()}** ({issue['severity']}): {issue['description']}\n"
            
            task_description += f"""

## Analysis Summary:
{self.analysis_results.get('summary', 'No summary available')}

## Recommendations:
"""
            for rec in self.analysis_results.get('recommendations', []):
                task_description += f"- {rec}\n"
            
            task_description += """

## Action Required:
Please review the DAP report, investigate the flagged issues, and take appropriate action.

## Resources:
- Full DAP Report: Available in workflow data
- Time-Series Data: Attached to workflow
- Historical Comparison: Available in analysis section
"""
            
            # Create task using BeeAI Framework
            task = Task(
                title=f"Review DAP Report Issues - {context.get('report_date')}",
                description=task_description,
                task_type="review",
                priority=priority,
                assigned_to=context.get('user_id', 'analyst'),
                workflow_id=self.workflow_id,
                workflow_instance_id=context.get('workflow_instance_id'),
                metadata={
                    'report_date': context.get('report_date'),
                    'risk_level': risk_level,
                    'issues_count': len(self.issues_found),
                    'issues': self.issues_found,
                    'analysis': self.analysis_results
                }
            )
            
            # Save task (implementation depends on your task management system)
            task_id = await self._save_task(task)
            
            return {
                'task_id': task_id,
                'priority': priority.value,
                'issues_count': len(self.issues_found)
            }
            
        except Exception as e:
            logger.error(f"Failed to create analyst task: {str(e)}", exc_info=True)
            return None
    
    async def _save_task(self, task: Task) -> str:
        """
        Save task to task management system.
        
        Args:
            task: Task object to save
            
        Returns:
            Task ID
        """
        # This is a placeholder - implement based on your task management system
        # For example, save to database, create Jira ticket, etc.
        task_id = f"DAP-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        logger.info(f"Task saved with ID: {task_id}")
        return task_id
    
    async def _create_user_toast(self, context: Dict[str, Any], issue_count: int) -> None:
        """
        Create a user toast notification for flagged issues.
        
        Args:
            context: Workflow context
            issue_count: Number of issues found
        """
        try:
            # Create toast notification (implementation depends on your notification system)
            toast_message = {
                'type': 'warning' if issue_count < 3 else 'error',
                'title': 'DAP Report Issues Detected',
                'message': f"{issue_count} issue(s) found in DAP report for {context.get('report_date')}. "
                          f"Please review the analyst task for details.",
                'duration': 10000,  # 10 seconds
                'user_id': context.get('user_id'),
                'action': {
                    'label': 'View Report',
                    'link': f"/reports/dap/{context.get('report_date')}"
                }
            }
            
            # Send toast (placeholder - implement based on your notification system)
            logger.info(f"Toast notification created for user {context.get('user_id')}: {toast_message['message']}")
            
        except Exception as e:
            logger.error(f"Failed to create user toast: {str(e)}", exc_info=True)


# Alias so registry finds the class (expects DapReportWorkflow from workflow_id "dap_report")
DapReportWorkflow = DAPReportWorkflow


def register_workflow():
    """Register the DAP Report workflow with the workflow registry."""
    return DAPReportWorkflow()