from web_server import app

version = '0.1.0'

if __name__ == '__main__' :
    
    print('------------------------------------------------')
    print('Hotlab CV - version ' + version)
    print('------------------------------------------------')
    
    app.run(host='0.0.0.0', port=5000)