desc 'build'
task :build do
	`rm -i dist/*`
	`./setup.py bdist_egg`
end

desc 'upload to cheese shop'
task :upload_ do
	`./setup.py bdist_egg upload`
end

desc 'clean'
task :clean do
	`rm -rf build dist`
end

desc 'copy (to=dest_dir)'
task :copy do
	dest = ENV['to'] or raise('please specify `to`')
	`rm -i "#{dest}/mocktest*.egg"`
	`cp -i dist/mocktest*.egg '#{dest}'`
	puts "Done!"
end
