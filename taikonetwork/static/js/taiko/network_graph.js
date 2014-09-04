function renderGraphOptions(s) {
  document.getElementById('refresh-btn').addEventListener('click', function() {
    var groupOption = $("input:radio[name = 'group-option']:checked").val();
    var genderFilter = $("input:radio[name = 'gender-filter']:checked").val();
    var lastGroupOption = document.getElementById('lastGroupOption').value;
    var lastGenderFilter = document.getElementById('lastGenderFilter').value;

    if (groupOption != lastGroupOption) {
      recolorNodes(s, demoColors[groupOption], groupOption);
      drawGroupLegend(demoColors[groupOption], groupOption);
      document.getElementById('lastGroupOption').value = groupOption;
    }
    if (genderFilter != lastGenderFilter) {
      filterNodes(s, genderFilter);
      document.getElementById('lastGenderFilter').value = genderFilter;
    }

    s.refresh();
  }, true);
}

function filterNodes(s, genderFilter) {
  var i,
      nodes = s.graph.nodes(),
      len = nodes.length;

  for (i = 0; i < len; i++) {
    if (nodes[i].data['gender'] == genderFilter || genderFilter == 'default') {
      nodes[i].hidden = false;
    } else {
      nodes[i].hidden = true;
    }
  }
}

function recolorNodes(s, colors, group) {
  var i,
      nodes = s.graph.nodes(),
      len = nodes.length;

  if (group == 'default') {
    for (i = 0; i < len; i++) {
      nodes[i].color = colors[i % 5];
    }
  } else {
    for (i = 0; i < len; i++) {
      nodes[i].color = colors[nodes[i].data[group]] || 'rgba(138, 138, 138, 0.7)';
    }
  }
}

function drawGroupLegend(colors, groupOption) {
  var box = document.getElementById('legend-box');
  var group_div = document.getElementById('legend-groups');
  group_div.innerHTML = '';

  if (groupOption == 'default') {
    box.style.display = 'none';
  } else {
    box.style.display = 'block';
    for (var key in colors) {
      group_div.innerHTML += '<div><div class="circle" ' +
        'style="background: ' + colors[key] + ';"></div>' + key + '</div>\n';
    }
    group_div.innerHTML += '<div><div class="circle" style="background: ' +
      'rgba(138, 138, 138, 0.7);"></div>No Data</div>';
  }
}

function setNodeSizeToDegree(s) {
  var i,
      nodes = s.graph.nodes(),
      len = nodes.length;

  for (i = 0; i < len; i++) {
    nodes[i].size = s.graph.degree(nodes[i].id);
  }
}

$(document).ready(function() {
  s = new sigma({
    graph: graphData,
    container: 'graph-container',
    renderer: {
      container: document.getElementById('graph-container'),
      type: 'canvas'
    },
    settings: {
      minNodeSize: 2,
      maxNodeSize: 12,
      minEdgeSize: 0.3,
      maxEdgeSize: 0.3,
      zoomingRatio: 1.3,
      drawLabels: false,
      drawEdges: false,
      edgeColor: 'default'
    }
  });

  setNodeSizeToDegree(s);

  s.refresh();
  s.startForceAtlas2();

});
