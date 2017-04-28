from idaapi import *
from idc import *
from idautils import *

from client import Client
from config import config

get_fhash = retrieve_input_file_sha256
fhash = None
client = Client(**config)

def onmsg(key, data):
    if key != fhash or key != retrieve_input_file_sha256():
        print 'hash mismatch, dropping command'
        return
    print 'msg', data

def on_load():
    global fhash
    if fhash:
        client.leave(fhash)
    fhash = get_fhash()
    client.join(fhash, onmsg)

class IDPHooks(IDP_Hooks):
    def renamed(self, ea, new_name, local_name):
        if isLoaded(ea):
            client.publish(get_fhash(), {'cmd': 'rename', 'addr': ea, 'text': new_name})
        return IDP_Hooks.renamed(self, ea, new_name, local_name)

    def newfile(self, fname):
        on_load()
        return IDP_Hooks.newfile(self, fname)

    def oldfile(self, fname):
        on_load()
        return IDP_Hooks.oldfile(self, fname)

class IDBHooks(IDB_Hooks):
    def cmt_changed(self, ea, repeatable):
        cmt = GetCommentEx(ea, repeatable)
        client.publish(get_fhash(), {'cmd': 'comment', 'addr': ea, 'text': cmt})
        return IDB_Hooks.cmt_changed(self, ea, repeatable)

    def extra_cmt_changed(self, ea, repeatable):
        cmt = GetCommentEx(ea, repeatable)
        client.publish(get_fhash(), {'cmd': 'extra_comment', 'addr': ea, 'text': cmt})
        return IDB_Hooks.extra_cmt_changed(self, ea, repeatable)

    def area_cmt_changed(self, cb, a, cmt, repeatable):
        client.publish(get_fhash(), {'cmd': 'area_comment', 'range': [a.startEA, a.endEA], 'text': cmt})
        return IDB_Hooks.area_cmt_changed(self, cb, a, cmt, repeatable)

hook1 = IDPHooks()
hook2 = IDBHooks()
hook1.hook()
hook2.hook()
