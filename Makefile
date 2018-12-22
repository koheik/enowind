
build/crawler.py: src/crawler.py
	mkdir -p build
	cp src/crawler.py build/.

build/updater.py: src/updater.py
	mkdir -p build
	cp src/updater.py build/.

package.zip: build/crawler.py build/updater.py
	pip install --target ./build requests beautifulsoup4
	cd build && zip -r9 ../package.zip .

package.yaml: template.yaml package.zip
	sam package \
		--template-file=template.yaml \
		--s3-bucket=enowind-package.koheik.com \
		--output-template-file=package.yaml

deploy: package.yaml
	sam deploy \
		--template-file=package.yaml \
		--stack-name=Enowind \
		--capabilities=CAPABILITY_IAM

test: package.zip
	sam local invoke CrawlerFunction --event event.json


clean:
	rm -rf package.zip package.yaml build
