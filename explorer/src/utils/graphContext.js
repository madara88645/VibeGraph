function uniqueValues(values) {
  return [...new Set(values)];
}

export function buildNodeGroundingContext({
  nodeId,
  allNodes = [],
  allEdges = [],
}) {
  if (!nodeId) {
    return { callers: [], callees: [], neighbors: [] };
  }

  // PERFORMANCE OPTIMIZATION (Bolt): Replaced array allocation and iteration
  // map/filter with a simple loop over elements.
  const knownNodeIds = new Set();
  for (let i = 0; i < allNodes.length; i++) {
    const id = allNodes[i].id;
    if (id) {
      knownNodeIds.add(id);
    }
  }

  const callers = [];
  const callees = [];

  for (let index = 0; index < allEdges.length; index += 1) {
    const edge = allEdges[index];
    const source = edge?.source;
    const target = edge?.target;
    if (!source || !target) {
      continue;
    }

    if (target === nodeId && knownNodeIds.has(source)) {
      callers.push(source);
    }
    if (source === nodeId && knownNodeIds.has(target)) {
      callees.push(target);
    }
  }

  const uniqueCallers = uniqueValues(callers);
  const uniqueCallees = uniqueValues(callees);
  const neighbors = uniqueValues([...uniqueCallers, ...uniqueCallees]);

  return {
    callers: uniqueCallers,
    callees: uniqueCallees,
    neighbors,
  };
}
