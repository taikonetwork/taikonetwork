// Start and stop force movement on home graph.
function controlForce(s) {
  var forceOn = true;
  _.$('force-control').addEventListener('click', function() {
    if (forceOn) {
      forceOn = false;
      s.stopForceAtlas2();
      s.settings({
        drawEdges: true
      });
      s.refresh();
      _.$('force-control').childNodes[0].nodeValue = 'PLAY';
    } else {
      forceOn = true;
      s.settings({
        drawEdges: false
      });
      s.refresh();
      s.startForceAtlas2();
      _.$('force-control').childNodes[0].nodeValue = 'PAUSE';
    }
  }, true);
}


$(document).ready(function() {
  sigma.parsers.json(graphData,
    {
      container: 'graph-container',
      renderer: {
        container: _.$('graph-container'),
        type: 'canvas'
      },
      settings: {
        defaultLabelColor: '#fff',
        defaultLabelSize: 14,
        defaultLabelBGColor: '#fff',
        defaultHoverColor: '#000',
        labelThreshold: 6,
        minNodeSize: 0.5,
        maxNodeSize: 5,
        minEdgeSize: 0.3,
        maxEdgeSize: 0.3,
        drawEdges: false,
        batchEdgesDrawing: true,
        edgeColor: 'default'
      }
    },
    function(s) {
      sigma.renderers.def = sigma.renderers.canvas
      sigma.plugins.dragNodes(s, s.renderers[0]);

      s.refresh();
      s.startForceAtlas2();

      controlForce(s);
    }
  );

  // Show login form on click.
  $('#exploreLoginModal').on('shown.bs.modal', function() {
    $('#username').focus();
  });
  _.$('explore-btn').addEventListener('click', function() {
   if (authenticated) {
    window.location='/map/';
   } else {
    $('#exploreLoginModal').modal({show: true});
   }
  });

});
