import random


def build_chart_paths(values, previous_values=None):
    """Build chart paths from server-side metric changes."""
    previous_values = previous_values or {}
    dimensions = {
        'online_users_value': 95,
        'order_completion_value': 50,
        'optimize_demand_value': 95,
        'order_quantity_value': 95,
    }
    charts = {}

    for field, height in dimensions.items():
        value = values.get(field, 0)
        previous = previous_values.get(field, value)
        direction = 1 if value > previous else -1 if value < previous else 0
        rng = random.Random(f'{field}:{value}:{previous}')
        points = []
        for index, x in enumerate((0, 24, 48, 72, 96, 120)):
            progress = index / 5
            trend = direction * progress * height * 0.22
            center = height * 0.56 - trend
            y = max(6, min(height - 8, center + rng.uniform(-height * 0.18, height * 0.18)))
            points.append((x, round(y, 1)))

        line = f'M{points[0][0]} {points[0][1]}'
        for index in range(1, len(points)):
            previous_x, previous_y = points[index - 1]
            x, y = points[index]
            midpoint = round((previous_x + x) / 2, 1)
            line += f' C{midpoint} {previous_y}, {midpoint} {y}, {x} {y}'

        charts[field] = {
            'line': line,
            'fill': f'{line} L120 {height} L0 {height} Z',
        }

    return charts
