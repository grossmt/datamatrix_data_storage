$(document).ready(
    update_log(),
    setInterval(update_log, 1000)
);


// $(function () {
//     update_log();
//     setInterval(update_log, 1000);
// });

function update_log() {
    var output = document.getElementById('output');
    var requester = new XMLHttpRequest();

    // requester.open('GET', '{{ url_for('log_stream') }}', true);
    requester.open(
        'GET',
        '{{ url_for('log_stream') }}',
        true
    );
    requester.send();

    setTimeout(function () {

        if ($(requester.responseText).text() != output.text()) {
            output.html("");
            output.insertAdjacentHTML("afterbegin", requester.responseText);
        }
        else {
            console.log("no new loigs")
        }
    }, 1000);
}

