from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import myutils
import simplejson as json
import time
import os
from api import internal

@login_required
def main(request):
    params = {}
    params['queries'] = myutils.call_api(request, 'ListQueries')
    querynames = request.GET.getlist('query') or None
    rank = 'genus'
    if querynames:
        entities = []
        samples = []
        datahash = {}
        filename = "/tmp/%s-%d.txt" %(request.user.username, int(time.time()))
        for query in querynames:
            dataset =  internal.GetDataset(request, params={'queryname': [query], 'projectID': [1], 'dataset': ['Data-16s'], 'category': [rank], 'method': ['RDP-0-5']})
            for d in dataset:
                if d.entity not in entities:
                    entities.append(d.entity)
                if d.sample not in samples:
                    samples.append(d.sample)
                    datahash[d.sample] = {'query' : [query]}
                datahash[d.sample][d.entity] = d.profile
                if query not in datahash[d.sample]['query']: datahash[d.sample]['query'].append(query)
        with open(filename, 'w') as f:
            f.write('Rank,Taxa,')
            for sample in samples: f.write(str(sample)+',')
            f.write('\n')
            for entity in entities:
                mycontent = rank+','+entity+','
                for sample in samples:
                    if entity in datahash[sample]: mycontent+=str(datahash[sample][entity])
                    else: mycontent += str('0')
		    mycontent+=','
                mycontent+='\n'
                f.write(mycontent)
        pca = myutils.runRscript('pca.R', filename)
        pca = pca.split('\n')
        pca.pop(0) 
        pca.pop() 
        finaldata = [{'name' : querynames[0], 'color': '#ff0000', 'data': []}, {'name': querynames[1], 'color': '#0000ff', 'data': []}, {'name': 'Both', 'color': '#00ff00', 'data' : []}]
        for row in pca:
            cols = row.split(',')
            sample = cols[0]
            if sample[0] == 'X': sample = sample[1:]
            xy = [float(cols[1]), float(cols[2])]
            if len(datahash[sample]['query']) > 1: finaldata[2]['data'].append(xy)
            elif querynames[0] in datahash[sample]['query']: finaldata[0]['data'].append(xy)
            else: finaldata[1]['data'].append(xy)
        os.remove(filename)
        return HttpResponse(json.dumps(finaldata), content_type="application/json")
    return render(request, 'pca.html', params)