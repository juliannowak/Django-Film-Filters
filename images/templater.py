#ok nvm, i spoke too soon :lol: right after i sent that PM everything went to hell.


#anyways, my vision for the template-er is just a textbox where the user can type their post and use keys/placeholders which will get "grepped" as a last step.
keys=["file_name", "video_duration", "file_hash"]
values=['name', 'time', "alphanumeric"]
grep_args = zip(keys,values)

def replace_placeholders(grep_args):
    for elem in list:
        run(elem,...) #TODO prepend grep to each tuple, since run can take string arr

#i just thought we would split up our work by files (and files by object).
#keeps it easy, and as long as we're not responsible for the same objects, there shouldn't be any [i]serious[/i] problems (me deleting or changing ur code)
#for the record, i'm not against versioning control, i just don't enjoy git... at all.
#i can totally use it tho; git clone and git push commit is all u need to contribute, in theory.
#you'll have to take care of all the merges.

#so maybe we should have objects:
# UploadRequest for building the cURL shell script binds
# UploadResponse for parsing the output of these.
# we could then put these in an uploader module
# we could have them as one object, but idk if i like that. feels crammed
#thoughts?

#if you're doing the GUI the feels like a kind of fair split (admitidly, mine seems a little easier)
#but i'll do as many hosts as i can, if you want me to :D
