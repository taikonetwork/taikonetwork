// DOM utility function
var _ = {
  $: function (id) {
    return document.getElementById(id);
  },

  show: function (id) {
    var elem = document.getElementById(id);
    elem.className = elem.className.replace(/(?:^|\s)hidden(?!\S)/g, '');
  },

  hide: function (id) {
    document.getElementById(id).className = 'hidden';
  }
};

var s,
    filter;


function search() {
  var output = [],
      term = _.$('search-term').value,
      results = _.$('search-results'),
      match = RegExp(term.toLowerCase());

  results.innerHTML = '';
  if (term.length < 3) {
      results.innerHTML = '<em>Search term must be a minimum of 3 letters.</em>';
  } else {
    s.graph.nodes().forEach(function(n) {
      match.test(n.label.toLowerCase()) && output.push({
        id: n.id,
        name: n.label
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

  _.show('search-results');
}

function clearSearch() {
  _.$('search-term').value = '';
  _.$('search-results').innerHTML = '';
  _.hide('search-results');
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

  _.show('info-pane');
  _.show('info-exit-btn');
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
  _.hide('info-pane');
  _.hide('info-exit-btn');

  // hide search results
  _.$('search-results').innerHTML = '';
  _.hide('search-results');

  // undo graph filers
  filter.undo().apply();
}

function setNodeProperties() {
  var i,
      nodes = s.graph.nodes(),
      len = nodes.length;

  for (i = 0; i < len; i++) {
    nodes[i].size = s.graph.degree(nodes[i].id);
    nodes[i].x = Math.cos(2 * i * Math.PI / len) - (2 * Math.random());
    nodes[i].y = Math.sin(2 * i * Math.PI / len) - (2 * Math.random());
  }
}


$(document).ready(function() {
  s = new sigma({
    graph: graphData,
    container: 'graph-container',
    renderer: {
      container: _.$('graph-container'),
      type: 'canvas'
    },
    settings: {
      minNodeSize: 2,
      maxNodeSize: 12,
      minEdgeSize: 0.3,
      maxEdgeSize: 0.3,
      zoomingRatio: 1.3,
      drawLabels: false,
      edgeColor: 'default',
      doubleClickEnabled: false
    }
  });
  setNodeProperties();
  filter = new sigma.plugins.filter(s);

  // Bind the events:
  s.bind('clickNode doubleClickNode', onClickNode);
  _.$('search-btn').addEventListener('click', search);

  s.refresh();
});
