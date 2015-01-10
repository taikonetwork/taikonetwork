$(document).ready(function() {
  d3.select(window).on('resize', throttle);

  var zoom = d3.behavior.zoom()
      .scaleExtent([1, 9])
      .on('zoom', move);
  var width = _.$('map-container').offsetWidth;
  var height = width / 2;
  var topo, projection, path, svg, g;
  var graticule = d3.geo.graticule();
  var tooltip = d3.select('#map-container').append('div').attr('class', 'tooltip hidden');
  var throttleTimer;

  setup(width,height);

  d3.json(worldMapData, function(error, world) {
    var countries = topojson.feature(world, world.objects.countries).features;
    topo = countries;
    draw(topo);
  });

  // Slider to filter groups by year
  $('#slider').slider({
    min: 1950,
    max: 2014,
    step: 1,
    value: [1950, 2014],
    tooltip: 'hide'
  });
  $('#year').val(formatYearLabel($('#slider').slider('getValue')));
  $('#slider').on('slide', function(e) {
    $('#year').val(formatYearLabel(e.value));
  });

  function formatYearLabel(range) {
    if (range[0] == range[1]) {
      return range[0];
    }
    return range[0] + ' - ' + range[1];
  }

  function setup(width,height) {
    projection = d3.geo.mercator()
      .translate([(width/2), (height/2)])
      .scale( width / 2 / Math.PI);

    path = d3.geo.path().projection(projection);

    svg = d3.select('#map-container').append('svg')
        .attr('width', width)
        .attr('height', height)
        .call(zoom)
        // .on('click', click)
        .append('g');

    g = svg.append('g');
  }


  function draw(topo) {
    svg.append('path')
       .datum(graticule)
       .attr('class', 'graticule')
       .attr('d', path);

    g.append('path')
     .datum({type: 'LineString', coordinates: [[-180, 0], [-90, 0], [0, 0], [90, 0], [180, 0]]})
     .attr('class', 'equator')
     .attr('d', path);

    var country = g.selectAll('.country').data(topo);
    country.enter().insert('path')
        .attr('class', 'country')
        .attr('d', path)
        .attr('id', function(d,i) { return d.id; })
        .attr('title', function(d,i) { return d.properties.name; });
        // .style('stroke', function(d, i) { return d.properties.color; });

    // Offsets for tooltips
    var offsetL = _.$('map-container').offsetLeft + 20;
    var offsetT = _.$('map-container').offsetTop + 10;

    // Tooltips (country names)
    country
      .on('mousemove', function(d,i) {
        var mouse = d3.mouse(svg.node()).map(function(d) { return parseInt(d); });

        tooltip.classed('hidden', false)
               .attr('style', 'left:' + (mouse[0] + offsetL) + 'px;top:' + (mouse[1] + offsetT) + 'px')
               .html(d.properties.name);
      })
      .on('mouseout', function(d,i) {
        tooltip.classed('hidden', true);
      });

      drawMarkers(groups);
      // Add map markers for each group
      // groups.forEach(function(i) {
      //   addMarker(i.lng, i.lat, i.name);
      // });
  }


  function redraw() {
    width = _.$('map-container').offsetWidth;
    height = width / 2;
    d3.select('svg').remove();
    setup(width,height);
    draw(topo);
  }


  function move() {
    var t = d3.event.translate;
    var s = d3.event.scale;
    zscale = s;
    var h = height/4;

    t[0] = Math.min(
      (width/height)  * (s - 1),
      Math.max( width * (1 - s), t[0] )
    );

    t[1] = Math.min(
      h * (s - 1) + h * s,
      Math.max(height  * (1 - s) - h * s, t[1])
    );

    zoom.translate(t);
    g.attr('transform', 'translate(' + t + ')scale(' + s + ')');

    // Adjust the country hover stroke width based on zoom level
    // d3.selectAll('.country').style('stroke-width', 1.5 / s);
  }


  function throttle() {
    window.clearTimeout(throttleTimer);
      throttleTimer = window.setTimeout(function() {
        redraw();
      }, 200);
  }


  // Geo translation on mouse click in map
  function click() {
    var latlon = projection.invert(d3.mouse(this));
    console.log(latlon);
  }


  // Function to add group markers to the map
  function addMarker(lng, lat, text) {
    var gmarker = g.append('g').attr('class', 'gmarker');
    var x = projection([lng, lat])[0];
    var y = projection([lng, lat])[1];

    gmarker.append('svg:circle')
           .attr('cx', x)
           .attr('cy', y)
           .attr('class', 'point')
           .attr('r', 3);

    // Conditional in case a point has no associated text
    if (text.length > 0) {
      gmarker.append('text')
             .attr('x', x+4)
             .attr('y', y+3)
             .attr('class', 'text')
             .text(text);
    }
  }

  // Batch draw markers to map by passing JSON data
  function drawMarkers(markerData) {
    var gmarker = g.selectAll('.gmarker')
          .data(markerData)
        .enter().append('circle')
          .attr('class', 'gmarker')
          .attr('cx', function(d) { return projection([d.lng, d.lat])[0]; })
          .attr('cy', function(d) { return projection([d.lng, d.lat])[1]; })
          .attr('class', 'point')
          .attr('r', 1)
          .attr('id', function(d) { return d.sf_id; })
          .attr('title', function(d) { return d.name });

    // Offsets for tooltips
    var offsetL = _.$('map-container').offsetLeft + 20;
    var offsetT = _.$('map-container').offsetTop + 10;

    // Tooltips (country names)
    gmarker
      .on('mousemove', function(d,i) {
        var mouse = d3.mouse(svg.node()).map(function(d) { return parseInt(d); });

        tooltip.classed('hidden', false)
               .attr('style', 'left:' + (mouse[0] + offsetL) + 'px;top:' + (mouse[1] + offsetT) + 'px')
               .html(d.name);
      })
      .on('mouseout', function(d,i) {
        tooltip.classed('hidden', true);
      });
  }

});
