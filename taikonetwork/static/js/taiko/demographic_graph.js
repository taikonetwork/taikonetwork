// DOM utility function
var _ = {
  $: function (id) {
    return document.getElementById(id);
  }
};
var filter;

function updateFilterControls(graph, filter) {
  var raceCategories = {},
      asianCategories = {};

  // Get categories
  graph.nodes().forEach(function(n) {
    raceCategories[n.data['race']] = true;
    asianCategories[n.data['asian_ethnicity']] = true;
  })

  // Add categories to appropriate select element
  var raceSelectElem = _.$('race-category');
  Object.keys(raceCategories).forEach(function(c) {
    if (c != 'None') {
      var optionElem = document.createElement('option');
      optionElem.text = c;
      raceSelectElem.add(optionElem);
    }
  });

  var asianSelectElem = _.$('asian-category');
  Object.keys(asianCategories).forEach(function(c) {
    if (c != 'None') {
      var optionElem = document.createElement('option');
      optionElem.text = c;
      asianSelectElem.add(optionElem);
    }
  });

  // Reset button
  _.$('reset-filter-btn').addEventListener('click', function(e) {
    _.$('gender-category').selectedIndex = 0;
    _.$('race-category').selectedIndex = 0;
    _.$('asian-category').selectedIndex = 0;
    filter.undo().apply();
  });
}


function renderNodeGroups(s) {
  _.$('regroup-btn').addEventListener('click', function() {
    var groupOption = $("input:radio[name = 'group-option']:checked").val();
    var lastGroupOption = _.$('lastGroupOption').value;

    if (groupOption != lastGroupOption) {
      _recolorNodes(s, demoColors[groupOption], groupOption);
      _drawGroupLegend(demoColors[groupOption], groupOption);
      _.$('lastGroupOption').value = groupOption;
      s.refresh();
    }
  }, true);
}


function _recolorNodes(s, colors, group) {
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


function _drawGroupLegend(colors, groupOption) {
  var box = _.$('legend-box');
  var group_div = _.$('legend-groups');
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


function createSlider() {
  $('#ageRangeSlider').slider({
    min: 1,
    max: 81,
    step: 1,
    value: [1, 81],
    tooltip: 'hide'
  });

  $('#ageRangeSlider').on('slide', function(e) {
    var startAge = e.value[0].toString();
    var endAge  = e.value[1].toString();
    var range = '';
    if (startAge == '81') { startAge = '81+'; }
    if (endAge == '81') { endAge = '80+'; }

    if (startAge == endAge) {
      range = endAge;
    } else {
      range = startAge + ' – ' + endAge;
    }

    $('#ageRangeVal').text(range);
    if (range == '1 – 80+') {
      $('#ageRangeVal').css('color', 'black');
    } else {
      $('#ageRangeVal').css('color', '#d9534f');
    }
  });
}


function setNodeSizeToDegree(s) {
  var i,
      nodes = s.graph.nodes(),
      len = nodes.length;

  for (i = 0; i < len; i++) {
    nodes[i].size = s.graph.degree(nodes[i].id);
  }
}

function applyGenderFilter(e) {
  var c = e.target[e.target.selectedIndex].value;
  filter
    .undo('gender-category')
    .nodesBy(function(n) {
      return !c.length || n.data['gender'] === c;
    }, 'gender-category')
    .apply();
}

function applyRaceFilter(e) {
  var c = e.target[e.target.selectedIndex].value;
  filter
    .undo('race-category')
    .nodesBy(function(n) {
      return !c.length || n.data['race'] === c;
    }, 'race-category')
    .apply();
}

function applyAsianEthnicityFilter(e) {
  var c = e.target[e.target.selectedIndex].value;
  filter
    .undo('asian-category')
    .nodesBy(function(n) {
      return !c.length || n.data['asian_ethnicity'] === c;
    }, 'asian-category')
    .apply();
}


$(document).ready(function() {
  createSlider();

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
      drawEdges: false,
      edgeColor: 'default'
    }
  });
  setNodeSizeToDegree(s);

  filter = new sigma.plugins.filter(s);
  updateFilterControls(s.graph, filter);
  _.$('gender-category').addEventListener('change', applyGenderFilter);
  _.$('race-category').addEventListener('change', applyRaceFilter);
  _.$('asian-category').addEventListener('change', applyAsianEthnicityFilter);

  renderNodeGroups(s);

  s.refresh();
  s.startForceAtlas2();
});
