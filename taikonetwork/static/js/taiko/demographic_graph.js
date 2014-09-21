var filter;


function renderFilterControls(filter) {
  // Add categories to appropriate select element
  var raceSelectElem = _.$('race-category');
  configData['race'].categories.forEach(function(c) {
    var optionElem = document.createElement('option');
    optionElem.text = c;
    raceSelectElem.add(optionElem);
  });

  var asianSelectElem = _.$('asian-category');
  configData['ethnicity'].categories.forEach(function(c) {
    var optionElem = document.createElement('option');
    optionElem.text = c;
    asianSelectElem.add(optionElem);
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

    if (groupOption !== lastGroupOption) {
      _recolorNodes(s, configData[groupOption].colors, groupOption);
      _drawGroupLegend(configData[groupOption], groupOption);
      _.$('lastGroupOption').value = groupOption;
      s.refresh();
    }
  }, true);
}


function _recolorNodes(s, colors, group) {
  var i,
      nodes = s.graph.nodes(),
      len = nodes.length;

  if (group === 'default') {
    for (i = 0; i < len; i++) {
      nodes[i].color = colors[i % 12];
    }
  } else {
    for (i = 0; i < len; i++) {
      nodes[i].color = colors[nodes[i].attributes[group]] || 'rgba(0, 0, 0, 0.8)';
    }
  }
}


function _drawGroupLegend(config, groupOption) {
  var box = _.$('legend-box');
  var group_div = _.$('legend-groups');
  group_div.innerHTML = '';

  if (groupOption === 'default') {
    box.style.display = 'none';
  } else {
    box.style.display = 'block';
    config.categories.forEach(function(c) {
      group_div.innerHTML += '<div><div class="node" ' +
          'style="background: ' + config.colors[c] + ';"></div>' + c + '</div>\n';
    });
    group_div.innerHTML += '<div><div class="node" style="background: ' +
      config.colors['None'] + ';"></div>No Data</div>';
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
    if (startAge === '81') { startAge = '81+'; }
    if (endAge === '81') { endAge = '80+'; }

    if (startAge === endAge) {
      range = endAge;
    } else {
      range = startAge + ' – ' + endAge;
    }

    $('#ageRangeVal').text(range);
    if (range === '1 – 80+') {
      $('#ageRangeVal').css('color', 'black');
    } else {
      $('#ageRangeVal').css('color', '#d9534f');
    }
  });
}

function setNodeProperties(s) {
  var i,
      nodes = s.graph.nodes(),
      len = nodes.length;

  for (i = 0; i < len; i++) {
    nodes[i].size = s.graph.degree(nodes[i].id);
  }
}

function setEdgeProperties(s) {
  var i,
      edges = s.graph.edges(),
      len = edges.length;

  for (i = 0; i < len; i++) {
    edges[i].type = 'curve';
  }
}

function applyGenderFilter(e) {
  var c = e.target[e.target.selectedIndex].value;
  filter
    .undo('gender-category')
    .nodesBy(function(n) {
      return !c.length || n.attributes['gender'] === c;
    }, 'gender-category')
    .apply();
}

function applyRaceFilter(e) {
  var c = e.target[e.target.selectedIndex].value;
  filter
    .undo('race-category')
    .nodesBy(function(n) {
      return !c.length || n.attributes['race'] === c || (c === 'Multiracial' && !(n.attributes['race'] in configData['race'].colors));
    }, 'race-category')
    .apply();
}

function applyAsianEthnicityFilter(e) {
  var c = e.target[e.target.selectedIndex].value;
  filter
    .undo('asian-category')
    .nodesBy(function(n) {
      var multiethnic = false;
      return !c.length || n.attributes['ethnicity'] === c || (c === 'Multiethnic' && !(n.attributes['ethnicity'] in configData['ethnicity'].colors));
    }, 'asian-category')
    .apply();
}


$(document).ready(function() {
  createSlider();

  sigma.parsers.json(graphData,
    {
      container: 'graph-container',
      renderer: {
        container: _.$('graph-container'),
        type: 'canvas'
      },
      settings: {
        minNodeSize: 2,
        maxNodeSize: 8,
        minEdgeSize: 0.3,
        maxEdgeSize: 0.5,
        zoomingRatio: 1.3,
        drawLabels: false,
        batchEdgesDrawing: true,
        edgeColor: 'default'
      }
    },
    function(s) {
      setNodeProperties(s);
      setEdgeProperties(s);

      filter = new sigma.plugins.filter(s);
      renderFilterControls(filter);
      _.$('gender-category').addEventListener('change', applyGenderFilter);
      _.$('race-category').addEventListener('change', applyRaceFilter);
      _.$('asian-category').addEventListener('change', applyAsianEthnicityFilter);

      renderNodeGroups(s);

      s.refresh();
    }
  );

});
