"""Explicit-input Fusion helpers and dependency-free geometry measurements.

No active-document globals or automatic execution. Fusion API objects are passed
by the caller; pure geometry uses one caller-declared unit throughout.
"""
import math


def batch_parameters(design, changes, value_input):
    """changes maps existing local parameter names to expressions; check success."""
    parameters, values = [], []
    for name, expression in changes.items():
        parameter = design.allParameters.itemByName(name)
        if parameter is None:
            raise ValueError('Unknown parameter: ' + name)
        parameters.append(parameter)
        values.append(value_input.createByString(str(expression)))
    if parameters and not design.modifyParameters(parameters, values):
        raise RuntimeError('Fusion rejected the parameter batch; inspect the current design.')


def delete_selected_parameters(parameters, names):
    """Delete only explicitly nominated names; stop if dependencies prevent progress.

    Verify absence: some API builds return true even when a parameter remains.
    Earlier successful deletions can persist if a later dependency blocks progress.
    """
    pending = list(dict.fromkeys(names))
    deleted = []
    while pending:
        remaining = []
        for name in reversed(pending):
            item = parameters.itemByName(name)
            if item is not None:
                item.deleteMe()
            if parameters.itemByName(name) is None:
                deleted.append(name)
            else:
                remaining.append(name)
        if len(remaining) == len(pending):
            raise RuntimeError('Parameter deletion blocked: ' + ', '.join(remaining) +
                               '; already absent/deleted: ' + ', '.join(deleted))
        pending = remaining
    return deleted


def temporary_overlap_mm3(manager, first_proxy, second_proxy, intersection_operation):
    """Measure copies in one assembly frame; failed Boolean is unknown, never zero."""
    first, second = manager.copy(first_proxy), manager.copy(second_proxy)
    if first is None or second is None or not manager.booleanOperation(first, second, intersection_operation):
        raise RuntimeError('Temporary intersection failed; overlap is unknown.')
    volume = first.volume * 1000  # Fusion internal cm^3 -> mm^3
    if not math.isfinite(volume) or volume < 0:
        raise RuntimeError('Intersection returned an invalid volume.')
    return volume


def section_bounds_mm(manager, body, planes):
    """Explicit station->Plane mapping; retain empty sections and evaluator errors."""
    result = []
    for station, plane in planes:
        row = {'station': station}
        try:
            section = manager.planeIntersection(body, plane)
            if section is None or not section.edges.count:
                row['status'] = 'empty'
            else:
                box = section.boundingBox
                row.update(status='measured', minimum_mm=[v * 10 for v in (box.minPoint.x, box.minPoint.y, box.minPoint.z)],
                           maximum_mm=[v * 10 for v in (box.maxPoint.x, box.maxPoint.y, box.maxPoint.z)])
        except Exception as exc:
            row.update(status='unknown', error=str(exc))
        result.append(row)
    return result


def point_triangle_distance_squared(point, triangle):
    """Exact distance to one triangle, including degenerate edges/vertices."""
    a, b, c = triangle
    def subtract(x, y):
        return tuple(u - v for u, v in zip(x, y))
    def dot(x, y):
        return sum(u * v for u, v in zip(x, y))
    def segment(x, y):
        edge, delta = subtract(y, x), subtract(point, x)
        length = dot(edge, edge)
        position = min(1, max(0, dot(delta, edge) / length)) if length else 0
        return sum((point[i] - x[i] - position * edge[i]) ** 2 for i in range(3))
    ab, ac, ap = subtract(b, a), subtract(c, a), subtract(point, a)
    normal = (ab[1]*ac[2]-ab[2]*ac[1], ab[2]*ac[0]-ab[0]*ac[2], ab[0]*ac[1]-ab[1]*ac[0])
    nn = dot(normal, normal)
    if nn > 0:
        d00, d01, d11 = dot(ab, ab), dot(ab, ac), dot(ac, ac)
        denominator = d00*d11 - d01*d01
        if denominator > 0:
            v = (d11*dot(ap, ab)-d01*dot(ap, ac))/denominator
            w = (d00*dot(ap, ac)-d01*dot(ap, ab))/denominator
            if v >= 0 and w >= 0 and v+w <= 1:
                return dot(ap, normal)**2/nn
    return min(segment(a, b), segment(b, c), segment(c, a))


def sampled_surface_distances(points, triangles, *, max_pairs=1000000):
    """Global nearest input triangle for each sample; explicit bound avoids hangs.

    This measures sampled points against a mesh, not continuous CAD equivalence.
    """
    points, triangles = list(points), list(triangles)
    if not points or not triangles or len(points)*len(triangles) > max_pairs:
        raise ValueError('Need nonempty mesh/samples within the explicit pair budget.')
    if any(not isinstance(t, (list, tuple)) or len(t) != 3 for t in triangles):
        raise ValueError('Each triangle needs three vertices.')
    vectors = points + [vertex for triangle in triangles for vertex in triangle]
    if any(not isinstance(v, (list, tuple)) or len(v) != 3 or any(not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x) for x in v) for v in vectors):
        raise ValueError('Geometry must contain finite 3D coordinates in one declared unit.')
    distances = [math.sqrt(min(point_triangle_distance_squared(p, t) for t in triangles)) for p in points]
    if not all(math.isfinite(value) for value in distances):
        raise ValueError('Coordinate scale overflowed the distance calculation.')
    ordered = sorted(distances)
    return dict(mean=sum(distances)/len(distances), p95=ordered[math.ceil(.95*len(ordered))-1],
                maximum=max(distances), worst_sample=list(points[distances.index(max(distances))]),
                samples=len(points), triangles=len(triangles), method='all-triangle point distances',
                continuous_equivalence_verified=False)
