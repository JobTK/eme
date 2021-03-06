import os
import zipfile



def zipdir(ziph, path, loc=None, exclude=None):
    nlist = ziph.namelist()

    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            name = root.replace('\\', '/') + '/' + file
            dirn = os.path.dirname(name)

            if '__pycache__' in name or '.log' in name or (exclude and dirn in exclude):
                continue

            if loc:
                lname = loc + '/' + file
                if lname not in nlist:
                    ziph.write(name, lname)
            else:
                if name not in nlist:
                    ziph.write(name)


zipf = zipfile.ZipFile('webapp.zip', 'w', zipfile.ZIP_DEFLATED)
zipdir(zipf, 'webapp')
zipf.write('run.py', 'run.py')
zipf.close()
os.replace('webapp.zip', '../eme_tools/content/webapp.zip')

zipf = zipfile.ZipFile('wsapp.zip', 'w', zipfile.ZIP_DEFLATED)
zipdir(zipf, 'wsapp')
zipf.write('runws.py', 'runws.py')
zipf.close()
os.replace('wsapp.zip', '../eme_tools/content/wsapp.zip')

zipf = zipfile.ZipFile('cliapp.zip', 'w', zipfile.ZIP_DEFLATED)
zipdir(zipf, 'cliapp')
zipf.write('cli.py', 'cli.py')
zipf.close()
os.replace('cliapp.zip', '../eme_tools/content/cliapp.zip')

zipf = zipfile.ZipFile('testapp.zip', 'w', zipfile.ZIP_DEFLATED)
zipdir(zipf, 'testapp')
zipf.write('cli.py', 'cli.py')
zipf.close()
os.replace('testapp.zip', '../eme_tools/content/testapp.zip')

zipf = zipfile.ZipFile('core.zip', 'w', zipfile.ZIP_DEFLATED)
zipdir(zipf, 'core')
zipf.close()
os.replace('core.zip', '../eme_tools/content/core.zip')
