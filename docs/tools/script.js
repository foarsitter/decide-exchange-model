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
});