#
# Given a module-list generated by findmodulefiles
# generate the resource file with all needed modules
#
import macfs
import py_resource
import Res
import sys

def main():
	fss, ok = macfs.PromptGetFile('Module sources listing:', 'TEXT')
	if not ok:
		sys.exit(0)
	ofss, ok = macfs.StandardPutFile('PYC resource output file:')
	if not ok:
		sys.exit(0)
	mfss, ok = macfs.PromptGetFile('Source for __main__ (or cancel):')
	if ok:
		mainfile = mfss.as_pathname()
	else:
		mainfile = None
	fp = open(fss.as_pathname())
	data = fp.read()
	modules = eval(data)
	
	fsid = py_resource.create(ofss.as_pathname(), creator='RSED')
	
	if mainfile:
		id, name = py_resource.frompyfile(mainfile, '__main__')
	for module, source in modules:
		if source:
			id, name = py_resource.frompyfile(source)
			print 'Wrote %d %s: %s'%(id, name, source)
			
	Res.CloseResFile(fsid)
	
if __name__ == '__main__':
	main()
	sys.exit(1)
