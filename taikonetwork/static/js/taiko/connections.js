function validateForm(e) {
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


$(document).ready(function() {
  $('#connections-form').on('submit', validateForm);

});
