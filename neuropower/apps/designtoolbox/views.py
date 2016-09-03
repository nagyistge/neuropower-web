from __future__ import unicode_literals
import sys
sys.path = sys.path[1:]
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, render_to_response
from django.conf import settings
from scipy.stats import norm, t
import os
from utils import get_session_id, probs_and_cons, get_design_steps, weights_html
from .forms import DesignMainForm,DesignConsForm,DesignReviewForm,DesignWeightsForm, DesignProbsForm, DesignOptionsForm, DesignRunForm, DesignDownloadForm
from .models import DesignModel
from designcore import design
import numpy as np
import time
import json
import pandas as pd
import csv
import zipfile
import StringIO
import shutil

## MAIN PAGE TEMPLATE PAGES

def FAQ(request):
    return render(request,"design/FAQ.html",{})

def tutorial(request):
    return render(request,"design/tutorial.html",{})

def methods(request):
    return render(request,"design/methods.html",{})

def start(request):

    # Get the template/step status

    template = "design/start.html"
    context = {}

    # Get the session ID and database entry

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template,sid)

    return render(request,template,context)

def maininput(request):

    # Get the template/step status

    template = "design/input.html"
    context = {}

    # Get the session ID and database entry

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template,sid)

    try:
        desdata = DesignModel.objects.get(SID=sid)
    except DesignModel.DoesNotExist:
        desdata = None

    # Define form

    inputform = DesignMainForm(request.POST or None,instance=desdata)

    # If page was result of POST or not valid: show form with db entries
    # Else: go to next page

    if not request.method=="POST" or not inputform.is_valid():
        context["inputform"] = inputform
        return render(request,template,context)
    else:

        # initial save

        form = inputform.save(commit=False)
        form.SID = sid
        form.mainpars = True
        form.save()

        # get data and change parameters

        desdata = DesignModel.objects.get(SID=sid)
        weightsform = DesignWeightsForm(None, instance=desdata)
        weightsform = weightsform.save(commit=False)
        W = np.array([desdata.W1,desdata.W2,desdata.W3,desdata.W4])
        if np.sum(W) != 1:
            W = W/np.sum(W)
        weightsform.W = W
        weightsform.save()

        return HttpResponseRedirect('../consinput/')

def consinput(request):

    # Get the template/step status

    template = "design/cons.html"
    context = {}

    # Get the session ID and database entry

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template,sid)

    try:
        desdata = DesignModel.objects.get(SID=sid)
    except DesignModel.DoesNotExist:
        return HttpResponseRedirect('../maininput/')

    # Define form

    consform = DesignConsForm(request.POST or None,instance=desdata,stim=desdata.S,cons=desdata.Clen)

    # If page was result of POST or not valid: show form with db entries
    # Else: go to next page

    if not request.method=="POST" or not consform.is_valid():
        context["consform"] = consform
        return render(request,template,context)
    else:
        form = consform.save(commit=False)
        form.SID = sid
        form.conpars = True
        form.save()

        # get data and change parameters

        consform = DesignProbsForm(None, instance=desdata)
        consform = consform.save(commit=False)
        matrices = probs_and_cons(sid)
        consform.P = matrices['P']
        consform.C = matrices['C']
        if desdata.HardProb==True:
            consform.G = 200
            consform.I = 100
        consform.save()

        return HttpResponseRedirect('../review/')

def review(request):

    # Get the template/step status

    template = "design/review.html"
    context = {}

    # Get the session ID and database entry

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template,sid)

    try:
        desdata = DesignModel.objects.get(SID=sid)
    except DesignModel.DoesNotExist:
        return HttpResponseRedirect('../maininput/')

    # Define form

    revform = DesignReviewForm(request.POST or None,instance=desdata)
    context["revform"] = revform

    # Set summary variables in context

    matrices = probs_and_cons(sid)
    context['ITImin']=desdata.ITImin
    context['ITImax']=desdata.ITImax
    context['TR']=desdata.TR
    context['S']=desdata.S
    context['L']=desdata.L
    context["Phtml"] = matrices["Phtml"]
    context["Chtml"] = matrices["Chtml"]
    context["Whtml"] = weights_html(desdata.W)
    context["order"] = desdata.ConfoundOrder
    context["repeat"] = desdata.MaxRepeat

    context["message"] = ""
    if desdata.HardProb==True:
        context["message"] = context["message"]+"<p><b>Warning:</b> Because of the hard limit on the frequencies, we increased the size of the generation and the number of random designs per generation.  This might slow down the optimisation.  </p>"
    if desdata.MaxRepeat<10 and desdata.S==2:
        context["message"] = context["message"]+"<p><b>Warning:</b> With only 2 stimuli, many random designs have repetitions larger dan "+str(desdata.MaxRepeat)+".  We increased the number of random designs per generation, but this might slow down the optimisation.  </p>"

    # If page was result of POST: show summary
    # Else: go to next page

    if not request.method=="POST":
        return render(request,template,context)
    else:
        form = revform.save(commit=False)
        form.SID = sid
        form.save()

        return HttpResponseRedirect('../runGA/')

def options(request):

    # Get the template/step status

    template = "design/options.html"
    context = {}

    # Get the session ID and database entry

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template,sid)

    try:
        desdata = DesignModel.objects.get(SID=sid)
    except DesignModel.DoesNotExist:
        return HttpResponseRedirect('../maininput/')

    # Define form

    opsform = DesignOptionsForm(request.POST or None,instance=desdata)
    context["opsform"] = opsform

    # If page was result of POST: show summary
    # Else: go to next page

    if not request.method=="POST":
        return render(request,template,context)
    else:
        form = opsform.save(commit=False)
        form.SID = sid
        form.save()
        return HttpResponseRedirect('../review/')

def runGA(request):

    # Get the template/step status

    template = "design/runGA.html"
    context = {}

    # Get the session ID and database entry

    sid = get_session_id(request)
    context["steps"] = get_design_steps(template,sid)

    # check if there is a database entry: else go back to inputform

    try:
        desdata = DesignModel.objects.get(SID=sid)
    except DesignModel.DoesNotExist:
        return HttpResponseRedirect('../maininput/')

    # Define form (Run or Stop)

    runform = DesignRunForm(request.POST or None,instance=desdata)
    context["runform"] = runform

    # Get parameters to GA

    matrices = probs_and_cons(sid)
    desfile = os.path.join(settings.MEDIA_ROOT,"designs","design_"+str(sid)+".json")
    genfile = os.path.join(settings.MEDIA_ROOT,"designs","generation_"+str(sid)+".json")
    onsetsfolder = os.path.join(settings.MEDIA_ROOT,"designonsets",str(sid))

    des = design.GeneticAlgorithm(
        # design specific
        ITI = [desdata.ITImin,desdata.ITImax],
        TR = desdata.TR,
        L = desdata.L,
        P = matrices["P"],
        C = matrices["C"],
        weights = desdata.W,
        ConfoundOrder = desdata.ConfoundOrder,
        MaxRepeat = desdata.MaxRepeat,
        # general/defaulted
        rho = desdata.rho,
        Aoptimality = True if desdata.Aoptimality==1 else False,
        saturation = True if desdata.Saturation==1 else False,
        resolution = desdata.resolution,
        G = desdata.G,
        q = desdata.q,
        I = desdata.I,
        cycles = desdata.cycles,
        preruncycles = desdata.preruncycles,
        write = genfile,
        HardProb = desdata.HardProb,
        tapsfile = os.path.join(settings.MEDIA_ROOT,"taps.p")
    )
    des.counter = 0

    # Responsive loop

    if request.method=="POST":
        form = runform.save(commit=False)

        # If stop is requested
        if request.POST.get("GA")=="Stop":

            form.stop = 1
            form.running = 0
            form.save()

            context["message"] = "Analysis halted."

        # If run is requested
        if request.POST.get("GA")=="Run":

            # check whether loop is already running and only start if it's not running
            desdata = DesignModel.objects.get(SID=sid)
            if not (desdata.running==0 or desdata.running==6):
                context["message"] = "Analysis is already running."

            else:
                form.running = 1
                form.stop = 0
                form.save()

                # Compute maximum efficiency
                desdata = DesignModel.objects.get(SID=sid)
                print("running maximum efficiency (Ff and Fc)")

                nulorder = [np.argmin(des.P)]*des.n_trials
                nulitis = [des.mnITI]*des.n_trials

                NulDesign = {"order":nulorder,"ITIs":nulitis}
                NulDesign = des.CreateDesignMatrix(NulDesign)
                des.FfMax = des.FfCalc(NulDesign)['Ff']
                des.FcMax = des.FcCalc(NulDesign)['Fc']

                # prerun for FeMax #
                if desdata.stop==0 and desdata.W1>0:
                    form.running = 2
                    form.save()
                    print("running maximum efficiency (Fe)")
                    des.prerun = 'Fe'
                    Generation = des.GeneticAlgorithmCreateEmptyGeneration()
                    des.GeneticAlgorithmCreateOrder()
                    weights = [0,0,1] if des.HardProb==True else [1/3.,1/3.,1/3.]
                    weights = [int(x) for x in np.array(weights)*des.G]
                    Generation = des.GeneticAlgorithmAddOrder(Generation,weights)
                    Best = []
                    gens=[]
                    for gen in range(des.preruncycles):
                        gens.append({"Gen":gen})
                        with open(genfile,'w') as outfile:
                            json.dump(gens,outfile)
                        des.counter = gen
                        desdata = DesignModel.objects.get(SID=sid)
                        if desdata.stop == 1:
                            form.running = 0
                            form.save()
                            break
                        print("Generation: "+str(gen+1))
                        NextGen = des.GeneticAlgorithmGeneration(Generation)
                        Generation = NextGen["NextGen"]
                        Best.append(NextGen['FBest'])
                        des.FeMax = Best[-1]

                # prerun for FdMax #
                if desdata.stop==0 and desdata.W2>0:
                    form.running = 3
                    form.save()
                    print("running maximum efficiency (Fd)")
                    des.prerun = 'Fd'
                    Generation = des.GeneticAlgorithmCreateEmptyGeneration()
                    des.GeneticAlgorithmCreateOrder()
                    weights = [0,0,1.] if des.HardProb==True else [1/3.,1/3.,1/3.]
                    weights = [int(x) for x in np.array(weights)*des.G]
                    Generation = des.GeneticAlgorithmAddOrder(Generation,weights)
                    Best = []
                    gens = []
                    for gen in range(des.preruncycles):
                        gens.append({"Gen":gen})
                        with open(genfile,'w') as outfile:
                            json.dump(gens,outfile)
                        des.counter = gen
                        desdata = DesignModel.objects.get(SID=sid)
                        if desdata.stop == 1:
                            form.running = 0
                            form.save()
                            break
                        print("Generation: "+str(gen+1))
                        NextGen = des.GeneticAlgorithmGeneration(Generation)
                        Generation = NextGen["NextGen"]
                        Best.append(NextGen['FBest'])
                        des.FdMax = Best[-1]

                # Initiate !
                des.prerun = None
                if desdata.stop==0:
                    form.running = 4
                    form.save()
                    des.GeneticAlgorithmCreateOrder()
                    Generation = des.GeneticAlgorithmCreateEmptyGeneration()
                    weights = [0,0,1] if des.HardProb==True else [1./3,1./3,1./3]
                    weights = [int(x) for x in np.array(weights)*des.G]
                    Generation = des.GeneticAlgorithmAddOrder(Generation,weights)

                # Run !
                if desdata.stop==0:
                    print("running genetic algorithm")
                    Results = []
                    form.running = 5
                    form.save()

                    Out = {"FBest":[],'FeBest':[],'FfBest':[],'FcBest':[],'FdBest':[],'Gen':[]}
                    keys = ["Stimulus_"+str(i) for i in range(desdata.S)]
                    Seq = {}
                    for s in keys:
                        Seq.update({s:[]})


                    for gen in range(desdata.cycles):
                        des.counter = gen
                        print("Generation: "+str(gen+1))
                        desdata = DesignModel.objects.get(SID=sid)
                        if desdata.stop == 1:
                            form.running = 0
                            form.save()
                            break
                        # check for convergence
                        last = len(Out['FBest'])-1
                        earlier = int(last - 100)
                        if gen>120 and (Out['FBest'][last] - Out['FBest'][earlier])<10**(-6):
                            form.running = 0
                            form.save()
                            convergence = True
                            break
                        NextGen = des.GeneticAlgorithmGeneration(Generation)
                        Generation = NextGen["NextGen"]

                        # write away optimality criteria
                        for key in ['FBest','FeBest','FfBest','FcBest','FdBest']:
                            Out[key].append(NextGen[key])
                        Out['Gen'].append(gen)
                        with open(genfile,'w') as outfile:
                            json.dump(Out,outfile)

                        if gen % 10 == 0: #only do this every 10 gens to save computing time
                            # write away best design
                            for stim in range(desdata.S):
                                Seq["Stimulus_"+str(stim)]=NextGen["Design"]["Xconv"][:,stim].tolist()
                            Seq.update({"tps":NextGen["Design"]["ts"].tolist()})
                            with open(desfile,'w') as out2file:
                                json.dump(Seq,out2file)
                    out2file.close()
                    outfile.close()
                    OptInd = np.min(np.arange(len(Generation['F']))[Generation['F']==np.max(Generation['F'])])
                    form.optimalorder = Generation['order'][OptInd]
                    form.optimalonsets = Generation['onsets'][OptInd]

                    desdata = DesignModel.objects.get(SID=sid)
                    if desdata.running==5:
                        form.running = 6
                        form.save()
                    context['message']="Analysis complete"
                    if convergence:
                        context['message']="Convergence reached: analysis complete"

            form.stop = 0
            if not desdata.optimalorder is None:
                form.running = 6
        form.save()

        if request.POST.get("Download")=="Download optimal sequence":
            orders = desdata.optimalorder
            onsets = [round(x/desdata.resolution)*desdata.resolution for x in desdata.optimalonsets]
            if os.path.exists(onsetsfolder):
                shutil.rmtree(onsetsfolder)
            os.mkdir(onsetsfolder)
            # http://stackoverflow.com/questions/12881294/django-create-a-zip-of-multiple-files-and-make-it-downloadable
            filenames = [os.path.join(onsetsfolder,"stimulus_"+str(stim)+".txt") for stim in range(desdata.S)]
            for stim in range(desdata.S):
                onsubsets = [str(x) for x in np.array(onsets)[np.array(orders)==stim]]
                f = open(filenames[stim],'w+')
                for line in onsubsets:
                    f.write(line)
                    f.write("\n")
                f.close()
            zip_subdir = "OptimalDesign"
            zip_filename = "%s.zip" % zip_subdir
            s = StringIO.StringIO()
            zf = zipfile.ZipFile(s,"w")
            for fpath in filenames:
                fdir, fname = os.path.split(fpath)
                zip_path = os.path.join(zip_subdir,fname)
                zf.write(fpath,zip_path)
            zf.close()

            resp = HttpResponse(s.getvalue(), content_type = "application/x-zip-compressed")
            resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename

            return resp

    else:
        desdata = DesignModel.objects.get(SID=sid)
        context["preruns"]=desdata.preruncycles
        context["runs"]=desdata.cycles
        context["refrun"]=0

        context["message"]=""
        if desdata.running==1:
            context["message"]="Design optimisation initiated."
            context["refrun"]="1"
        elif desdata.running==2:
            context["message"]="Running first pre-run to find maximum efficiency."
            context["refrun"]="1"
        elif desdata.running==3:
            context["message"]="Running second pre-run to find maximum power."
            context["refrun"]="2"
        elif desdata.running==4:
            context["message"]="Starting design optimisation."
            context["refrun"]="3"
        elif desdata.running==5:
            context["message"]="Design optimisation running."
            context["refrun"]="3"
        elif desdata.running==6:
            context["message"]="Design optimisation done"
            context['refrun']="3"
            downform = DesignDownloadForm(request.POST or None,instance=desdata)
            context["downform"] = downform
            downform = downform.save(commit=False)

        if os.path.isfile(genfile):
            jsonfile = open(genfile).read()
            try:
                data = json.loads(jsonfile)
                data = json.dumps(data)
                context['optim']=data
            except ValueError:
                pass

        if os.path.isfile(desfile):
            jsonfile = open(desfile).read()
            try:
                data = json.loads(jsonfile)
                data = json.dumps(data)
                context['design']=data
                context['stim']=desdata.S
            except ValueError:
                pass

    return render(request,template,context)

def updatepage(request):
    return render(request,"design/updatepage.html",{})



### SESSION CONTROL

def end_session(request):
    '''ends a session so the user can start a new one.'''
    try:
        request.session.flush()
    except KeyError:
        pass
    return neuropowerinput(request,end_session=True)
