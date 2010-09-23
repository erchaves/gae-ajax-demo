(function($){
    //avoid colllisions with other plugins using $

    //$() is okay - will be called in a $(document).ready
    function updateNode($node, urlPath, cacheBool) {
        $.ajax({
            url: urlPath,
            cache: cacheBool,
            success: function(frag){
                $node.html(frag);
            //console.log(frag);
            }
        });
    };

    //using polling for now - Change this when google launches their Channel API (see http://www.youtube.com/watch?v=oMXe-xK0BWA, http://groups.google.com/group/google-appengine/browse_thread/thread/48d459f522d257d1?tvc=2)
    $(document).ready(function() {

        //just testing this out - make solution more general later...
        $("#chatContent").bind('update', function(e){
            updateNode( $(this), "/messages", false);
        });

        var updateNodes = function(){
            updateNode( $("#chatContent"), "/messages", false);
        //make multiple updates
        //updateNode( $(someother), "/somepath", false);
        //updateNode( $(andanother), "/someotherpath", false);
        };
        //do once at the start
        updateNodes();
        setInterval(updateNodes, 1500);
    });
})(jQuery);