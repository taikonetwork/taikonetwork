// DOM utility function
var _ = {
  $: function (id) {
    return document.getElementById(id);
  }
};
var s,
    filter;


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
  infoProfile.innerHTML += '<img src="/static/images/profile.png" alt="Profile Image" id="profile-img" class="img-thumbnail">\n';
  infoProfile.innerHTML += '<h4>' + node.label + '</h4>\n';
  infoProfile.innerHTML += '<a href="#">View Profile</a>\n';

  var infoConnections = _.$('info-connections-list');
  infoConnections.innerHTML = '';
  neighbors.forEach(function(n) {
    infoConnections.innerHTML += '<li><a href="#">' + n.label + '</a></li>\n'
  });

  $('#info-pane').show();
  $('#info-exit-btn').show();
}

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

function resetGraphCanvas() {
  // hide info pane
  _.$('info-profile').innerHTML = '';
  _.$('info-connections-list').innterHTML = '';
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
});
