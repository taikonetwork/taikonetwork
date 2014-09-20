function validateForm(e) {
  $('#form-error-alert').hide();
  $('#query-error').hide();
  $('#query-success').hide();
  _.$('graph-container').innerHTML = '';

  // Validate form.
  var error = false;
  if ($('#firstname1').val()=='') {
    $('#fg-first1').addClass('has-error');
    error = true;
  }
  if ($('#lastname1').val()=='') {
    $('#fg-last1').addClass('has-error');
    error = true;
  }
  if ($('#firstname2').val()=='') {
    $('#fg-first2').addClass('has-error');
    error = true;
  }
  if ($('#lastname2').val()=='') {
    $('#fg-last2').addClass('has-error');
    error = true;
  }

  if (error) {
    e.preventDefault();
    $('#form-error-alert').show();
  } else {
    // Do nothing and let form submit.
  }
}


function renderGraph(graph) {
  // Get node indices for links.
  var edges = [];
  graph.edges.forEach(function(e) {
    var srcNode = graph.nodes.filter(function(n) { return n.id === e.source; })[0],
        endNode = graph.nodes.filter(function(n) { return n.id === e.target; })[0];
    edges.push({source: srcNode, target: endNode, label: e.label});
  });

  var width = 1080;
  var height = 960;

  var force = d3.layout.force()
      .size([width, height])
      .charge([-650])
      .linkDistance([350])
      .on('tick', tick)
      .nodes(graph.nodes)
      .links(edges)
      .start();

  var svg = d3.select('#graph-container').append('svg');

  var drag = force.drag()
      .on('dragstart', dragstart);

  var link = svg.selectAll('.link')
      .data(force.links())
    .enter().append('line')
      .attr('class', 'link')
      .attr('id', function(d,i) { return 'e_' + i; });

  var node = svg.append('g').selectAll('.node')
      .data(force.nodes())
    .enter().append('circle')
      .attr('r', 20)
      .attr('class', 'node')
      .style('fill',
          function(d) {
            if (d.color === 1) {
              return '#f00';
            }
          }
      )
      .on('dblclick', dblclick)
      .call(drag);

  var nodeLabel = svg.append('g').selectAll('.nodelabel')
      .data(force.nodes())
    .enter().append('text')
      .attr('class', 'nodelabel')
      .attr('x', 23)
      .attr('y', '.30em')
      .text(function(d) { return d.label; });

  var edgePath = svg.selectAll('.edgepath')
      .data(force.links())
    .enter().append('path')
      .attr('d', function(d) {return 'M '+ d.source.x +' ' + d.source.y + ' L ' + d.target.x + ' ' + d.target.y})
      .attr('class', 'edgepath')
      .attr('id', function(d,i) { return 'ep_' + i; });

  var edgeLabel = svg.selectAll('.edgelabel')
        .data(force.links())
      .enter().append('text')
        .attr('class', 'edgelabel')
        .attr('dx', 85)
        .attr('dy', '-.24em')
        .attr('id', function(d,i) { return 'el_' + i; });

  edgeLabel.append('textPath')
        .attr('xlink:href', function(d,i) { return '#ep_' + i; })
        .style('pointer-events', 'none')
        .text(function(d) { return d.label; });


  function tick() {
    link.attr('x1', function(d) { return d.source.x; })
        .attr('y1', function(d) { return d.source.y; })
        .attr('x2', function(d) { return d.target.x; })
        .attr('y2', function(d) { return d.target.y; });

    edgePath.attr('d', function(d) {
      var path = 'M ' + d.source.x + ' ' + d.source.y + ' L ' + d.target.x + ' ' + d.target.y;
      return path;
    });

    edgeLabel.attr('transform', function(d) {
      if (d.target.x < d.source.x) {
        bbox = this.getBBox();
        rx = bbox.x + bbox.width / 2;
        ry = bbox.y + bbox.height / 2;
        return 'rotate(180 ' + rx + ' ' + ry + ')';
      } else {
        return 'rotate(0)';
      }
    });

    node.attr('transform', transform);
    nodeLabel.attr('transform', transform);
  }

  function transform(d) {
    return 'translate(' + d.x + ',' + d.y + ')';
  }

  function dblclick(d) {
    d3.select(this).classed('fixed', d.fixed = false);
  }

  function dragstart(d) {
    d3.select(this).classed('fixed', d.fixed = true);
  }
}

function processQuery() {
  var query_params = {
    'first1': _.$('firstname1').value,
    'last1': _.$('lastname1').value,
    'first2': _.$('firstname2').value,
    'last2': _.$('lastname2').value,
  }

  $.ajax({
    url: 'query',
    type: 'GET',
    data: query_params,
    success: function(data) {
      if (data['error_msg']) {
        _.$('query-error').innerHTML = '<p>' + data['error_msg'] + '</p>'
        $('#query-error').show();
      } else {
        _.$('query-success').innerHTML = '<p>' + data['member1']
          + '<span class="glyphicon glyphicon-resize-horizontal icon-sep2"></span>'
          + data['member2'] + '<span class="icon-sep2"><strong>|</strong></span>'
          + 'Degrees of Separation: ' + data['degrees'] + '</p>';
        $('#query-success').show();
        var graph = data['graph'];
        renderGraph(graph);
      }
    },
    failure: function(data) {
      _.$('query-error').innerHTML = '<p><strong>ERROR:</strong> Unable to process request. Please try again.</p>'
      $('#query-error').show();
    }
  });
}


$(document).ready(function() {
  $('#connections-form').on('submit', validateForm);
});
