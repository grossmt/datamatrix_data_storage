// $(document).ready(

// );

function update_log() {
    var output = document.getElementById('output');
    var requester = new XMLHttpRequest();

    requester.open('GET', '{{ url_for('log_stream') }}', true);
    requester.send();

    setTimeout(function () {
        if ($(requester.responseText).text() != $('#output').text()) {
            $('#output').html("");
            output.insertAdjacentHTML("afterbegin", requester.responseText);
        }
    }, 1000);
}

// update_log();
// setInterval(update_log, 1000);