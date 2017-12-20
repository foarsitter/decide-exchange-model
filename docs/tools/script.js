$(function () {


    var container = $("#actor-issues tbody");

    $("#actors, #issues").change(function () {
        container.html("");
        update_actor_issues();

    })




    update_actor_issues();

    function update_actor_issues() {
        var actors = $("#actors").val().split("\n");
        var issues = $("#issues").val().split("\n");

        for (var j = 0; j < issues.length; j++) {

            var issue_name = issues[j].trim();

            if (issue_name !== "") {

                container.append('<tr class="bg-secondary"><th colspan="99">' + issue_name + '</th></tr>');

                for (var i = 0; i < actors.length; i++) {
                    if (issues[j].trim() !== "" && actors[i].trim() !== "") {
                        var child = $('<tr />');
                        child.append('<td>' + actors[i].trim() + '</td>');
                        child.append('<td>' + issue_name + '</td>');
                        child.append(return_input());
                        child.append(return_input());
                        child.append(return_input());
                        container.append(child);
                    }

                }
            }
        }

    }

    function return_input() {

        var input = $('<input />').attr('type', 'number').addClass('form-control');

        var td = $('<td />');

        td.append(input);

        return td;
    }

    function fileInfo(e) {
            var file = e.target.files[0];
            if (file.name.split(".")[1].toUpperCase() != "CSV") {
                alert('Invalid csv file !');
                e.target.parentNode.reset();
                return;
            } else {
                document.getElementById('file_info').innerHTML = "<p>File Name: " + file.name + " | " + file.size + " Bytes.</p>";
            }
        }


        function handleFileSelect() {


            var file = document.getElementById("the_file").files[0];
            var reader = new FileReader();

            reader.onload = function (file) {

                var actors = [];
                var issues = [];
                var data = [];
                var content = file.target.result;
                var rows = file.target.result.split(/[\r\n|\n]+/);


                for (var i = 0; i < rows.length; i++) {

                    var arr = rows[i].split('\t'); // TODO make a sniffer

                    if (arr[0] === rows[i] && rows['i'] !== '' || arr.length === 0) {
                        console.log('wrong split char');
                        arr = rows[i].split(';');
                    }

                    if (arr.length > 0) {
                        if (arr[0] === "#A") {
                            actors.push(arr[1])
                        }

                        if (arr[0] === "#P") {
                            issues.push(arr[1])
                        }
                    }
                }
                console.log(actors);
                console.log(issues);

                update_actors(actors);
                update_issues(issues);
                update_actor_issues()
            };
            reader.readAsText(file);
        }

        function update_actors(actors) {
            var textarea = $('#actors');

            textarea.val('')

            for (var i = 0; i < actors.length; i++) {
                textarea.val(textarea.val() + actors[i] + '\n');
            }
        }

        function update_issues(issues) {
            var textarea = $('#issues');

            textarea.val('');

            for (var i = 0; i < issues.length; i++) {
                textarea.val(textarea.val() + issues[i] + '\n');
            }
        }

        document.getElementById('the_form').addEventListener('submit', handleFileSelect, false);
        document.getElementById('the_file').addEventListener('change', fileInfo, false);
});