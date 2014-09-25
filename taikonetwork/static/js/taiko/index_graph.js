function controlForce(s) {
  var forceOn = true;
  document.getElementById('force-control').addEventListener('click', function() {
    if (forceOn) {
      forceOn = false;
      s.stopForceAtlas2();
      s.settings({
        drawEdges: true
      });
      s.refresh();
      document.getElementById('force-control').childNodes[0].nodeValue = 'PLAY';
    } else {
      forceOn = true;
      s.settings({
        drawEdges: false
      });
      s.refresh();
      s.startForceAtlas2();
      document.getElementById('force-control').childNodes[0].nodeValue = 'PAUSE';
    }
  }, true);
}


$(document).ready(function() {
  sigma.parsers.json(graphData,
    {
      container: 'graph-container',
      renderer: {
        container: document.getElementById('graph-container'),
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

});
