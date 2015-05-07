var s,
    filter;

// Add a method to the graph model that returns an
// object with every neighbors of a node inside:
sigma.classes.graph.addMethod('neighbors', function(id) {
  if (typeof id !== 'string')
        throw 'neighbors: the node id must be a string.';
  var k,
      neighbors = [];

  for(k in this.allNeighborsIndex[id]) {
    neighbors.push(this.nodesIndex[k]);
  }
  return neighbors;
});


function searchNodes() {
  var output = [],
      term = _.$('search-term').value,
      results = _.$('search-results'),
      match = RegExp(term.toLowerCase());

  results.innerHTML = '';
  if (term.length < 3) {
      results.innerHTML = '<em>Search term must be a minimum of 3 letters.</em>';
  } else {
    s.graph.nodes().forEach(function(n) {
      node_label = n.label;
      match.test(node_label.toLowerCase()) && output.push({
        id: n.id,
        name: node_label
      });
    });
    results.innerHTML = '<strong>Search Results: </strong>';
    if (output.length < 1) {
      results.innerHTML += '<em>No results found.</em>';
    } else {
      output.forEach(function(o) {
        results.innerHTML += '<li><a href="javascript:void(0);" onclick="onSearchNode(\''+ o.id +'\')">' + o.name + '</a></li>';
      });
    }
  }

  $('#search-results').show();
}

function clearSearch() {
  _.$('search-term').value = '';
  _.$('search-results').innerHTML = '';
  $('#search-results').hide();
}

function onSearchNode(id) {
  var node = s.graph.nodes(id);
  displayFilterNodeInfo(node);
}

function onClickNode(e) {
  var node = e.data.node;
  displayFilterNodeInfo(node);
}

function toggleMetrics() {
  var metrics = _.$('metrics-info');
  if (metrics.style.display == 'block') {
    metrics.style.display = 'none';
  } else {
    metrics.style.display = 'block';
  }
}

function displayFilterNodeInfo(node) {
  var neighbors = s.graph.neighbors(node.id);

  // Filter all nodes except clicked node + neighbors
  filter
    .undo()
    .neighborsOf(node.id)
    .apply();

  // Display information of clicked node
  var infoProfile = _.$('info-profile');
  infoProfile.innerHTML = '';
  infoProfile.innerHTML += '<img src="/static/images/taiko.png" alt="TaikoNetwork Node" id="profile-img" style="background-color:' + node.color +'" class="img-circle">\n';
  infoProfile.innerHTML += '<h3>' + node.label + '</h3>\n';
  infoProfile.innerHTML += '<a href="javascript:void(0);" onclick="toggleMetrics()">'
    + '<h4><span class="caret"></span> Metrics <span class="caret"></span></h4></a> \n'
    + '<div id="metrics-info"><h5>Triadic Closure</h5><ul class="info-pane-text">\n'
    + '<li>Number of Triangles: <strong>' + node.attributes['Number of triangles'] + '</strong></li>\n'
    + '<li>Clustering Coefficient: <strong>' + parseFloat(node.attributes['Clustering Coefficient']).toPrecision(3) + '</strong></li></ul>\n'
    + '<h5>Centrality Measures</h5><ul class="info-pane-text">\n'
    + '<li>Degree: <strong>' + node.attributes['Degree'] + '</strong></li>\n'
    + '<li>Closeness: <strong>' + parseFloat(node.attributes['Closeness Centrality']).toPrecision(6) + '</strong></li>\n'
    + '<li>Betweenness: <strong>' + parseFloat(node.attributes['Betweenness Centrality']).toPrecision(6) + '</strong></li>\n'
    + '<li>Eccentricity: <strong>' + node.attributes['Eccentricity'] + '</strong></li>\n'
    + '<li>Eigenvector: <strong>' + parseFloat(node.attributes['Eigenvector Centrality']).toPrecision(6) + '</strong></li>\n'
    + '</ul></div>\n';

  var infoConnections = _.$('info-connections-list');
  infoConnections.innerHTML = '';
  neighbors.forEach(function(n) {
    infoConnections.innerHTML += '<li><a href="javascript:void(0);" onclick="onSearchNode(\''+ n.id +'\')">' + n.label + '</a></li>\n';
  });

  $('#info-pane').show();
  $('#info-exit-btn').show();
}

function resetGraphCanvas() {
  // hide info pane
  _.$('info-profile').innerHTML = '';
  _.$('info-connections-list').innerHTML = '';
  $('#info-pane').hide();
  $('#info-exit-btn').hide();

  // hide search results
  _.$('search-results').innerHTML = '';
  $('#search-results').hide();

  // undo graph filers
  filter.undo().apply();
}

function setEdgeProperties() {
  var i,
      edges = s.graph.edges(),
      len = edges.length;

  for (i = 0; i < len; i++) {
    edges[i].type = 'curve';
  }
}

function setNodeProperties() {
  var i,
      nodes = s.graph.nodes(),
      len = nodes.length;

  for (i = 0; i < len; i++) {
    nodes[i].size = s.graph.degree(nodes[i].id);
  }
}


$(document).ready(function() {
  var g = {
    nodes: [],
    edges: []
  };

  s = new sigma({
    graph: graphData,
    container: 'graph-container',
    renderer: {
      container: _.$('graph-container'),
      type: 'canvas'
    },
    settings: {
      labelThreshold: 8,
      minNodeSize: 2,
      maxNodeSize: 6,
      minEdgeSize: 0.3,
      maxEdgeSize: 0.5,
      edgeColor: 'default',
      batchEdgesDrawing: true,
      doubleClickEnabled: false
    }
  });

  sigma.parsers.json(
    graphData,
    s,
    function() {
      setNodeProperties();
      setEdgeProperties();
      filter = new sigma.plugins.filter(s);

      // Bind the events:
      s.bind('clickNode doubleClickNode', onClickNode);
      _.$('search-btn').addEventListener('click', searchNodes, true);

      s.refresh();
    }
  );

  $('#exit-click-link').click(function() {
    resetGraphCanvas();
    return false;
  });

});
