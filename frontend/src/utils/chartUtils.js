export const autoDetectChartConfig = (data, columns) => {
    if (!columns || columns.length === 0 || !data || data.length === 0) {
        return null;
    }

    const rows = data;

    // Find numeric and categorical columns
    const numericColumns = [];
    const categoricalColumns = [];

    columns.forEach(col => {
        const sampleValue = rows[0][col];
        if (typeof sampleValue === 'number') {
            numericColumns.push(col);
        } else {
            categoricalColumns.push(col);
        }
    });

    // Determine chart type based on data structure
    let chartType = 'bar';
    let xKey = categoricalColumns[0] || columns[0];
    let yKeys = numericColumns.length > 0 ? numericColumns : [columns[1] || columns[0]];

    // If we have a date/time column, suggest line chart
    const dateColumns = columns.filter(col =>
        col.toLowerCase().includes('date') ||
        col.toLowerCase().includes('time') ||
        col.toLowerCase().includes('year') ||
        col.toLowerCase().includes('month')
    );

    if (dateColumns.length > 0) {
        chartType = 'line';
        xKey = dateColumns[0];
    }

    // If we have only one numeric column and few categories, suggest pie chart
    if (numericColumns.length === 1 && categoricalColumns.length === 1 && rows.length <= 8) {
        chartType = 'pie';
    }

    return {
        type: chartType,
        xKey,
        yKeys,
        title: 'Data Visualization'
    };
};

export const transformResultsToChartData = (results) => {
    if (!results || !results.rows || results.rows.length === 0) {
        return [];
    }

    // Attempt to convert numeric strings to numbers for visualization
    return results.rows.map(row => {
        const newRow = { ...row };
        Object.keys(newRow).forEach(key => {
            const val = newRow[key];
            if (typeof val === 'string' && !isNaN(val) && val.trim() !== '') {
                // Check if it really looks like a number (not just a date string that parses to number?)
                // Simple float parse
                newRow[key] = parseFloat(val);
            }
        });
        return newRow;
    });
};
