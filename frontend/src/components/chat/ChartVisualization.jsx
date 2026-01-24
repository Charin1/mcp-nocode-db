import React from 'react';
import {
    BarChart, Bar, LineChart, Line, PieChart, Pie, AreaChart, Area,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts';
import { autoDetectChartConfig, transformResultsToChartData } from '../../utils/chartUtils';

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c43', '#00C49F', '#FFBB28', '#FF8042', '#0088FE'];


const ChartVisualization = ({ results, chartConfig }) => {
    const data = transformResultsToChartData(results);
    const config = chartConfig || autoDetectChartConfig(data, results?.columns);

    if (!data || data.length === 0 || !config) {
        return (
            <div className="text-center text-gray-400 py-4">
                Unable to generate visualization for this data.
            </div>
        );
    }

    const { type, xKey, yKeys, title } = config;

    const renderChart = () => {
        switch (type) {
            case 'line':
                return (
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis dataKey={xKey} stroke="#9CA3AF" fontSize={12} />
                        <YAxis stroke="#9CA3AF" fontSize={12} />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: '#1F2937',
                                border: '1px solid #374151',
                                borderRadius: '8px'
                            }}
                        />
                        <Legend />
                        {yKeys.map((key, index) => (
                            <Line
                                key={key}
                                type="monotone"
                                dataKey={key}
                                stroke={COLORS[index % COLORS.length]}
                                strokeWidth={2}
                                dot={{ fill: COLORS[index % COLORS.length] }}
                            />
                        ))}
                    </LineChart>
                );

            case 'pie':
                const pieDataKey = yKeys[0];
                return (
                    <PieChart>
                        <Pie
                            data={data}
                            dataKey={pieDataKey}
                            nameKey={xKey}
                            cx="50%"
                            cy="50%"
                            outerRadius={80}
                            label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                        >
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip
                            contentStyle={{
                                backgroundColor: '#1F2937',
                                border: '1px solid #374151',
                                borderRadius: '8px'
                            }}
                        />
                        <Legend />
                    </PieChart>
                );

            case 'area':
                return (
                    <AreaChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis dataKey={xKey} stroke="#9CA3AF" fontSize={12} />
                        <YAxis stroke="#9CA3AF" fontSize={12} />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: '#1F2937',
                                border: '1px solid #374151',
                                borderRadius: '8px'
                            }}
                        />
                        <Legend />
                        {yKeys.map((key, index) => (
                            <Area
                                key={key}
                                type="monotone"
                                dataKey={key}
                                stroke={COLORS[index % COLORS.length]}
                                fill={COLORS[index % COLORS.length]}
                                fillOpacity={0.3}
                            />
                        ))}
                    </AreaChart>
                );

            case 'bar':
            default:
                return (
                    <BarChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis dataKey={xKey} stroke="#9CA3AF" fontSize={12} />
                        <YAxis stroke="#9CA3AF" fontSize={12} />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: '#1F2937',
                                border: '1px solid #374151',
                                borderRadius: '8px'
                            }}
                        />
                        <Legend />
                        {yKeys.map((key, index) => (
                            <Bar
                                key={key}
                                dataKey={key}
                                fill={COLORS[index % COLORS.length]}
                                radius={[4, 4, 0, 0]}
                            />
                        ))}
                    </BarChart>
                );
        }
    };

    return (
        <div className="mt-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>
            <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                    {renderChart()}
                </ResponsiveContainer>
            </div>
            <div className="mt-3 flex justify-center space-x-2">
                <ChartTypeSelector config={config} />
            </div>
        </div>
    );
};

const ChartTypeSelector = ({ config }) => {
    return (
        <div className="flex space-x-1 text-xs text-gray-400">
            <span>Chart Type: </span>
            <span className="text-blue-400 font-medium capitalize">{config.type}</span>
        </div>
    );
};

export default ChartVisualization;
