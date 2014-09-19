// DOM utility function
var _ = {
  $: function (id) {
    return document.getElementById(id);
  }
};

function clearInput(id) {
  _.$(id).value = '';
}
