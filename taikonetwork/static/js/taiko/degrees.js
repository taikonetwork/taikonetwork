function validateForm(e) {
  // Validate form.
  var error = false;
  if ($('#firstname').val()=='') {
    $('#fg-degree-first').addClass('has-error');
    error = true;
  }
  if ($('#lastname').val()=='') {
    $('#fg-degree-last').addClass('has-error');
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
  $('#degrees-form').on('submit', validateForm);
});
