"""
Visualization Service for generating chart configurations from query results.
Uses LLM to intelligently determine the best visualization based on data and user intent.
"""
from typing import Dict, Any, List, Optional


class VisualizationService:
    """Service for analyzing data and generating chart configurations."""

    # Supported chart types
    CHART_TYPES = ['bar', 'line', 'pie', 'area']

    def analyze_data_for_chart(self, columns: List[str], rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze query results to determine the best chart type and configuration.
        
        Args:
            columns: List of column names
            rows: List of row dictionaries
            
        Returns:
            Chart configuration dictionary
        """
        if not columns or not rows:
            return None

        # Classify columns by data type
        numeric_columns = []
        categorical_columns = []
        date_columns = []

        for col in columns:
            sample_value = rows[0].get(col)
            
            # Check for date-like column names
            if any(keyword in col.lower() for keyword in ['date', 'time', 'year', 'month', 'day', 'timestamp']):
                date_columns.append(col)
            elif isinstance(sample_value, (int, float)):
                numeric_columns.append(col)
            else:
                categorical_columns.append(col)

        # Determine chart type based on data structure
        chart_type = 'bar'  # default
        x_key = None
        y_keys = []

        if date_columns:
            # Time series data -> line chart
            chart_type = 'line'
            x_key = date_columns[0]
            y_keys = numeric_columns if numeric_columns else [columns[1] if len(columns) > 1 else columns[0]]
        elif len(categorical_columns) == 1 and len(numeric_columns) == 1 and len(rows) <= 8:
            # Single category and value with few items -> pie chart
            chart_type = 'pie'
            x_key = categorical_columns[0]
            y_keys = numeric_columns
        else:
            # Default to bar chart
            x_key = categorical_columns[0] if categorical_columns else columns[0]
            y_keys = numeric_columns if numeric_columns else [columns[1] if len(columns) > 1 else columns[0]]

        return {
            'type': chart_type,
            'xKey': x_key,
            'yKeys': y_keys,
            'title': self._generate_title(x_key, y_keys),
            'columns': columns,
            'numericColumns': numeric_columns,
            'categoricalColumns': categorical_columns,
            'dateColumns': date_columns
        }

    def _generate_title(self, x_key: str, y_keys: List[str]) -> str:
        """Generate a descriptive title for the chart."""
        if not y_keys:
            return 'Data Visualization'
        
        y_labels = ', '.join(y_keys)
        return f'{y_labels} by {x_key}' if x_key else f'{y_labels} Distribution'

    def suggest_alternative_charts(self, config: Dict[str, Any]) -> List[str]:
        """
        Suggest alternative chart types based on the current configuration.
        
        Args:
            config: Current chart configuration
            
        Returns:
            List of alternative chart type suggestions
        """
        current_type = config.get('type', 'bar')
        alternatives = []

        # Based on data characteristics, suggest alternatives
        has_time_series = bool(config.get('dateColumns'))
        num_categories = len(config.get('categoricalColumns', []))
        num_numeric = len(config.get('numericColumns', []))

        if current_type != 'bar':
            alternatives.append('bar')
        if current_type != 'line' and (has_time_series or num_categories == 1):
            alternatives.append('line')
        if current_type != 'area' and (has_time_series or num_categories == 1):
            alternatives.append('area')
        if current_type != 'pie' and num_numeric == 1 and num_categories == 1:
            alternatives.append('pie')

        return alternatives

    def generate_chart_config_from_intent(
        self, 
        user_request: str, 
        columns: List[str], 
        rows: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate chart configuration based on user's natural language request.
        
        Args:
            user_request: User's visualization request
            columns: Available column names
            rows: Query result rows
            
        Returns:
            Chart configuration based on user intent
        """
        # Start with auto-detected config
        config = self.analyze_data_for_chart(columns, rows)
        
        if not config:
            return None

        # Override chart type based on keywords in user request
        request_lower = user_request.lower()
        
        if 'pie' in request_lower or 'percentage' in request_lower or 'distribution' in request_lower:
            config['type'] = 'pie'
        elif 'line' in request_lower or 'trend' in request_lower or 'over time' in request_lower:
            config['type'] = 'line'
        elif 'area' in request_lower or 'filled' in request_lower:
            config['type'] = 'area'
        elif 'bar' in request_lower or 'comparison' in request_lower:
            config['type'] = 'bar'

        return config
