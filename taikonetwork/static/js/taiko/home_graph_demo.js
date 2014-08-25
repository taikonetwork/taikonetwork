function controlForce(sig) {
  var forceOn = true;
  document.getElementById('force-control').addEventListener('click', function() {
    if (forceOn) {
      forceOn = false;
      sig.stopForceAtlas2();
      sig.settings({
        drawEdges: true
      });
      sig.refresh();
      document.getElementById('force-control').childNodes[0].nodeValue = 'PLAY';
    } else {
      forceOn = true;
      sig.settings({
        drawEdges: false
      });
      sig.refresh();
      sig.startForceAtlas2();
      document.getElementById('force-control').childNodes[0].nodeValue = 'PAUSE';
    }
  }, true);
}

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
    s.refresh();
    s.startForceAtlas2();

    controlForce(s);
  }
);