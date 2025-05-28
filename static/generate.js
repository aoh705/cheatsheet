function generate_sheet(){
    $('#actions-submit-btn').click(function () {
        const selectedActions = $('input[name="actions"]:checked')
            .map(function () {
                return $(this).val();
            }).get();

        if (selectedActions.length > 0) {
            console.log('You selected: ' + selectedActions.join(', '));
        } else {
            console.log('No topics selected');
        }

        // send to generate cheat sheet
        $.ajax({
            type: "POST",
            url: "/generate_sheet",                
            dataType : "json",
            contentType: "application/json; charset=utf-8",
            data : JSON.stringify(selectedActions),
            beforeSend: function () { 
                $("#spinner-div").show();
            },
            success: function(result){
                let path = result['path_to_file']
                
                // create download link
                $('#download-link').attr('href', '/download') // Set the download URL
                                    .text('Download cheat sheet as PDF')
                                    .show();
                
            },
            error: function(request, status, error){
                console.log("Error");
                console.log(request)
                console.log(status)
                console.log(error)
            },
            complete: function () { 
                $("#spinner-div").hide()
            },
        });
    
    });
}

function generate_options(){
    $('#topics-submit-btn').click(function () {
        const selectedTopics = $('input[name="topics"]:checked')
            .map(function () {
                return $(this).val();
            }).get();

        if (selectedTopics.length > 0) {
            console.log('You selected: ' + selectedTopics.join(', '));
        } else {
            console.log('No topics selected');
        }

        // send to generate cheat sheet
        $.ajax({
            type: "POST",
            url: "/generate_actions",                
            dataType : "json",
            contentType: "application/json; charset=utf-8",
            data : JSON.stringify(selectedTopics),
            beforeSend: function () { 
                $("#spinner-div").show();
            },
            success: function(result){
                let actions = result['options']
    
                for(let i = 0; i < actions.length; i++){
                    let action = actions[i]
    
                    if(actions != ""){
                        const checkbox = $('<input>')
                            .attr('type', 'checkbox')
                            .attr('id', action)
                            .attr('value', action)
                            .attr('name', 'actions');

                        const label = $('<label>')
                            .attr('for', action)
                            .text(action)
                            .addClass('checkbox-label');

                        const listItem = $('<div>')
                            .addClass('checkbox-container')
                            .append(checkbox)
                            .append(label);

                        $('#actions-list').append(listItem);
                    }
                    
                }
                
            },
            error: function(request, status, error){
                console.log("Error");
                console.log(request)
                console.log(status)
                console.log(error)
            },
            complete: function () { 
                $("#spinner-div").hide()
            },
        });
        
        generate_sheet()
    
    });

}

function get_quiz(rec_data){
    $.ajax({
        type: "POST",
        url: "/topics", 
        data: rec_data,               
        dataType : false,
        processData: false,
        contentType: false,
        beforeSend: function () { 
            $("#spinner-div").show();
        },
        success: function(result){
            let subject = result['subject']
            let topics = result["topics"]
            $('#class-subject').html(`<p>${subject}</p>`)

            for(let i = 0; i < topics.length; i++){
                let topic = topics[i]

                if(topic != ""){
                    const checkbox = $('<input>')
                        .attr('type', 'checkbox')
                        .attr('id', topic)
                        .attr('value', topic)
                        .attr('name', 'topics');

                    const label = $('<label>')
                        .attr('for', topic)
                        .text(topic)
                        .addClass('checkbox-label');

                    const listItem = $('<div>')
                        .addClass('checkbox-container')
                        .append(checkbox)
                        .append(label);

                    $('#topics-list').append(listItem);
                }
                
            }
            
        },
        error: function(request, status, error){
            console.log("Error");
            console.log(request)
            console.log(status)
            console.log(error)
        },
        complete: function () { 
            $("#spinner-div").hide()
        },
    });

    generate_options()
}

function get_data(){
    // send subject to main to update rec_data[]
    $('#submit-subject-btn').click(function() {
        var subject = $('#subject').val();
        var major = $('#major').val()
        console.log(subject)
        console.log(major)

        info = {
            "major": major,
            "subject": subject
        }

        $.ajax({
            type: "POST",
            url: "/user",                
            dataType : "json",
            contentType: "application/json; charset=utf-8",
            data : JSON.stringify(info),
            beforeSend: function () { 
                $("#spinner-div").show();
            },
            success: function(result){
                let data = result["subject"]
                $('#class-subject').html(`<p>${data}</p>`)
                
            },
            error: function(request, status, error){
                console.log("Error");
                console.log(request)
                console.log(status)
                console.log(error)
            },
            complete: function () { 
                $("#spinner-div").hide()
            },
        });
    });

    // upload files to uploads folder
    $('#upload-files').on('click', function(){
        console.log("here")
        var formData = new FormData(); // Create FormData object
        
        var input = document.getElementById('file-upload');
        var files = input.files;
        for (var i = 0; i < files.length; i++) {
            formData.append('file', files[i]); // Append files to formData object
        }

        $.ajax({
            type: "POST",
            url: "/upload",                
            contentType: "application/json; charset=utf-8",
            data : formData,
            processData: false,
            contentType: false,
            beforeSend: function () { 
                $("#spinner-div").show();
            },
            success: function(result){
                message = result['message']
                subject = result["subject"]

                console.log(message)
                console.log(subject)

                $('#server-response').html(message);
                alert(message)
                $('#class-subject').html(`<p>${subject}</p>`)

                get_quiz(result)
                
            },
            error: function(request, status, error){
                console.log("Error");
                console.log(request)
                console.log(status)
                console.log(error)
            },
            complete: function () { 
                $("#spinner-div").hide()
            },
        });
    });

    $('#topics-list').empty();
    $('#actions-list').empty();
    $('#download-link').hide();
}

$(document).ready(function(){
    get_data();
});